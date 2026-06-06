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

    var searchText: String = "" {
        didSet {
            print("Search: \(searchText)")
            if searchText != oldValue { reload() }
        }
    }

    var sortOrder: [KeyPathComparator<Transmission>] = [.init(\.startTime)] {
        didSet {
            print("Sort: \(sortOrder)")
            if !sortOrderEquals(sortOrder, oldValue) { reload() }
        }
    }

    private let database: TransmissionDatabase?
    private var pages: [Int: [Transmission]] = [:]
    private let pageSize: Int = 1000

    init(database: TransmissionDatabase?) {
        self.database = database
        reload()
    }

    func transmission(at index: Int) -> Transmission {
        print("Fetching txn at index \(index)...")
        let pageIndex = index / pageSize
        let local = index - (pageIndex * pageSize)
        if let page = pages[pageIndex], local < page.count {
            print("\tfound cached at page \(pageIndex), #\(local)")
            return page[local]
        }
        guard let database else {
            print("\tNo database, using placeholder...")
            return placeholder(at: index)
        }
        do {
            let rows = try database.transmissions(
                matching: searchText,
                orderBy: sqlOrderClause,
                offset: pageIndex * pageSize,
                limit: pageSize,
            )
            pages[pageIndex] = rows
            print("\tFetched \(rows.count) rows for page \(pageIndex)")
            if local < rows.count {
                print("\tfound at page \(pageIndex), #\(local)")
                return rows[local]
            } else {
                print("\toverrun (\(local) >= \(rows.count)); using placeholder")
                return placeholder(at: index)
            }
        } catch {
            print("\terror (\(error)); using placeholder")
            return placeholder(at: index)
        }
    }

    func transmission(forID id: Transmission.ID) -> Transmission? {
        print("Getting txn for ID \(id)...")
        for page in pages.values {
            if let match = page.first(where: { $0.id == id }) {
                return match
            }
        }
        return nil
    }

    var rows: TransmissionRows { TransmissionRows(list: self) }

    private func reload() {
        print("Reloading DB...")
        guard let database else {
            return;
        }
        pages.removeAll()
        do {
            totalCount = try database.count(matching: searchText)
        } catch {
            totalCount = 0
        }
        dataVersion &+= 1
    }

    private var sqlOrderClause: String {
        guard let first = sortOrder.first else { return "order by START_TIME asc, rowid asc" }
        let column = sqlColumn(for: first.keyPath)
        let direction = first.order == .forward ? "asc" : "desc"
        return "order by \(column) \(direction), rowid asc"
    }

    private func sqlColumn(for keyPath: PartialKeyPath<Transmission>) -> String {
        if keyPath == \Transmission.eventID { return "EVENT_ID" }
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
        print("Fetching txn row at index \(position)...")
        return list.transmission(at: position)
    }
}
