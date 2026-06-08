//
//  TransmissionList.swift
//  Transmissions
//

import Foundation
import SwiftUI

@MainActor
@Observable
final class TransmissionList {
    private(set) var totalCount: Int = 0
    private(set) var dataVersion: Int = 0
    private(set) var isFullTextIndexReady: Bool = false
    private(set) var isLoading: Bool = false

    var searchText: String = "" {
        didSet {
            if searchText != oldValue { scheduleReload() }
        }
    }

    var sortOrder: [KeyPathComparator<Transmission>] = [.init(\.startTime)] {
        didSet {
            if !sortOrderEquals(sortOrder, oldValue) { scheduleReload() }
        }
    }

    private let database: TransmissionDatabase?
    private var pages: [Int: [Transmission]] = [:]
    private let pageSize: Int = 1000
    private var reloadTask: Task<Void, Never>?
    private var pageTasks: [Int: Task<Void, Never>] = [:]
    private var bumpTask: Task<Void, Never>?

    init(database: TransmissionDatabase?) {
        self.database = database
        scheduleReload()
        guard let database else { return }
        Task.detached(priority: .userInitiated) { [weak self] in
            do {
                try database.setupFullTextIndex()
            } catch {
                print("Unable to load database: \(error)")
                return
            }
            await self?.fullTextIndexDidSetup()
        }
    }

    private func fullTextIndexDidSetup() {
        isFullTextIndexReady = true
        if !searchText.isEmpty { scheduleReload() }
    }

    func transmission(at index: Int) -> Transmission {
        let pageIndex = index / pageSize
        let local = index - (pageIndex * pageSize)
        if let page = pages[pageIndex], local < page.count {
            return page[local]
        }
        loadPage(pageIndex)
        return placeholder(at: index)
    }

    func transmission(forID id: Transmission.ID) -> Transmission? {
        for page in pages.values {
            if let match = page.first(where: { $0.id == id }) {
                return match
            }
        }
        return nil
    }

    var rows: TransmissionRows { TransmissionRows(list: self) }

    private func scheduleReload() {
        reloadTask?.cancel()
        for (_, task) in pageTasks { task.cancel() }
        pageTasks.removeAll()
        bumpTask?.cancel()
        bumpTask = nil
        reloadTask = Task { [weak self] in
            await self?.performReload()
        }
    }

    private func performReload() async {
        guard let database else { return }
        let searchText = self.searchText
        let isIndexReady = self.isFullTextIndexReady
        let orderClause = self.sqlOrderClause
        let pageSize = self.pageSize
        isLoading = true

        // Fetch count and page 0 together so the table can render real rows
        // immediately rather than placeholders that flash to real data.
        async let countResult = Self.fetchCount(
            database: database,
            searchText: searchText,
            isIndexReady: isIndexReady,
        )
        async let firstPageResult = Self.fetchPage(
            database: database,
            searchText: searchText,
            isIndexReady: isIndexReady,
            orderClause: orderClause,
            pageIndex: 0,
            pageSize: pageSize,
        )
        let count = await countResult
        let firstPage = await firstPageResult

        guard !Task.isCancelled else {
            isLoading = false
            return
        }
        pages.removeAll()
        pages[0] = firstPage
        totalCount = count
        isLoading = false
        dataVersion &+= 1
    }

    nonisolated private static func fetchCount(
        database: TransmissionDatabase,
        searchText: String,
        isIndexReady: Bool,
    ) async -> Int {
        await Task.detached(priority: .userInitiated) {
            do {
                if searchText.isEmpty {
                    return try database.count()
                } else if isIndexReady {
                    return try database.count(matching: searchText)
                } else {
                    return 0
                }
            } catch {
                return 0
            }
        }.value
    }

    private func loadPage(_ pageIndex: Int) {
        if pageTasks[pageIndex] != nil { return }
        guard let database else { return }
        let searchText = self.searchText
        let isIndexReady = self.isFullTextIndexReady
        let orderClause = self.sqlOrderClause
        let pageSize = self.pageSize

        pageTasks[pageIndex] = Task { [weak self] in
            let rows = await Self.fetchPage(
                database: database,
                searchText: searchText,
                isIndexReady: isIndexReady,
                orderClause: orderClause,
                pageIndex: pageIndex,
                pageSize: pageSize,
            )
            guard let self else { return }
            self.pageTasks[pageIndex] = nil
            guard !Task.isCancelled else { return }
            self.pages[pageIndex] = rows
            self.scheduleBump()
        }
    }

    nonisolated private static func fetchPage(
        database: TransmissionDatabase,
        searchText: String,
        isIndexReady: Bool,
        orderClause: String,
        pageIndex: Int,
        pageSize: Int,
    ) async -> [Transmission] {
        await Task.detached(priority: .userInitiated) {
            do {
                if searchText.isEmpty {
                    return try database.transmissions(
                        orderBy: orderClause,
                        offset: pageIndex * pageSize,
                        limit: pageSize,
                    )
                } else if isIndexReady {
                    return try database.transmissions(
                        orderBy: orderClause,
                        offset: pageIndex * pageSize,
                        limit: pageSize,
                        matching: searchText,
                    )
                } else {
                    return []
                }
            } catch {
                return []
            }
        }.value
    }

    // Coalesce dataVersion bumps so multiple page loads in quick succession
    // only force one Table rebuild.
    private func scheduleBump() {
        bumpTask?.cancel()
        bumpTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 200_000_000)
            guard !Task.isCancelled else { return }
            self?.dataVersion &+= 1
        }
    }

    private var sqlOrderClause: String {
        guard let first = sortOrder.first else { return "order by START_TIME asc, rowid asc" }
        let column = sqlColumn(for: first.keyPath)
        let direction = first.order == .forward ? "asc" : "desc"
        return "order by \(column) \(direction), rowid asc"
    }

    private func sqlColumn(for keyPath: PartialKeyPath<Transmission>) -> String {
        if keyPath == \Transmission.eventID { return "EVENT" }
        if keyPath == \Transmission.station { return "STATION" }
        if keyPath == \Transmission.system { return "SYSTEM" }
        if keyPath == \Transmission.channel { return "CHANNEL" }
        if keyPath == \Transmission.startTime { return "START_TIME" }
        if keyPath == \Transmission.duration.orZero { return "DURATION" }
        if keyPath == \Transmission.transcription.orEmpty { return "TRANSCRIPTION" }
        return "START_TIME"
    }

    private func sortOrderEquals(
        _ a: [KeyPathComparator<Transmission>],
        _ b: [KeyPathComparator<Transmission>],
    ) -> Bool {
        guard a.count == b.count else { return false }
        return zip(a, b).allSatisfy { $0.keyPath == $1.keyPath && $0.order == $1.order }
    }

    private func placeholder(at index: Int) -> Transmission {
        Transmission(
            startTime: Date(timeIntervalSince1970: TimeInterval(index * 60)),
            eventID: "",
            station: "",
            system: "",
            channel: "",
            duration: nil,
            path: "",
            sha256: nil,
            transcription: "(placeholder #\(index))",
            transcriptionVersion: nil,
        )
    }
}

struct TransmissionRows: RandomAccessCollection {
    let list: TransmissionList

    var startIndex: Int { 0 }
    var endIndex: Int { list.totalCount }

    subscript(position: Int) -> Transmission {
        return list.transmission(at: position)
    }
}
