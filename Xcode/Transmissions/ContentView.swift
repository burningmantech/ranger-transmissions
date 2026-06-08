//
//  ContentView.swift
//  Transmissions
//
//  Created by Wilfredo Sánchez Vega on 5/28/26.
//

import SwiftUI
import UniformTypeIdentifiers

extension Optional where Wrapped == String {
    var orEmpty: Wrapped {
        self ?? ""
    }
}

extension Optional where Wrapped == Duration {
    var orZero: Wrapped {
        self ?? Duration.seconds(0)
    }
}

struct Transmission: Identifiable {
    let startTime: Date
    let eventID: String
    let station: String
    let system: String
    let channel: String
    let duration: Duration?
    let path: String
    let sha256: String?
    let transcription: String?
    let transcriptionVersion: Int?

    var id: Int {
        var hasher = Hasher()
        hasher.combine(eventID)
        hasher.combine(system)
        hasher.combine(channel)
        hasher.combine(startTime)
        return hasher.finalize()
    }
}

struct ContentView: View {
    @State private var searchText: String = ""
    @State private var selectedTransmissionID: Transmission.ID?
    @State private var transmissionList: TransmissionList?
    @State private var loadError: String?
    @State private var isImporting: Bool = false

    var selectedTransmission: Transmission? {
        guard let selectedTransmissionID else { return nil }
        return transmissionList?.transmission(forID: selectedTransmissionID)
    }

    var body: some View {
        VStack {
            TransmissionSearchBarView(
                searchText: $searchText,
                isEnabled: transmissionList?.isFullTextIndexReady ?? false,
            )
            if let loadError {
                Text(loadError)
                    .foregroundStyle(.red)
            } else if let transmissionList {
                TransmissionTableView(
                    transmissionList: transmissionList,
                    selectedTransmissionID: $selectedTransmissionID,
                )
                Text("\(transmissionList.totalCount) transmissions")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                TransmissionDetailsView(transmission: selectedTransmission)
                    .frame(height: 150)
            } else {
                Spacer()
                Button("Open Database…") { isImporting = true }
                Spacer()
            }
        }
        .padding()
        .fileImporter(
            isPresented: $isImporting,
            allowedContentTypes: [
                UTType(filenameExtension: "sqlite") ?? .data,
                .data,
            ]
        ) { result in
            switch result {
            case .success(let url):
                openDatabase(at: url)
            case .failure(let error):
                loadError = error.localizedDescription
            }
        }
        .task(id: searchText) {
            try? await Task.sleep(nanoseconds: 200_000_000)
            guard !Task.isCancelled else { return }
            transmissionList?.searchText = searchText
        }
    }

    private func openDatabase(at url: URL) {
        let needsRelease = url.startAccessingSecurityScopedResource()
        defer { if needsRelease { url.stopAccessingSecurityScopedResource() } }
        do {
            let database = try TransmissionDatabase(url: url)
            transmissionList = TransmissionList(database: database)
            selectedTransmissionID = nil
            loadError = nil
        } catch {
            loadError = "Failed to open database: \(error)"
            transmissionList = nil
        }
    }
}

struct TransmissionTableView: View {
    @Bindable var transmissionList: TransmissionList
    @Binding var selectedTransmissionID: Transmission.ID?

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "EE MM/dd HH:mm"
        return formatter
    }()

    private let durationStyle = Duration.TimeFormatStyle(pattern: .hourMinuteSecond(padHourToLength: 2))

    var body: some View {
        VStack {
            Table(transmissionList.rows, selection: $selectedTransmissionID, sortOrder: $transmissionList.sortOrder) {
                TableColumn("Event ID", value: \.eventID)
                    .width(50)
                TableColumn("Station", value: \.station)
                    .width(125)
                TableColumn("System", value: \.system)
                    .width(60)
                TableColumn("Time", value: \.startTime) { transmission in
                    Text(dateFormatter.string(from: transmission.startTime))
                }
                .width(110)
                TableColumn("Channel", value: \.channel)
                    .width(110)
                TableColumn("Duration", value: \.duration.orZero) { transmission in
                    Text(transmission.duration?.formatted(durationStyle) ?? "")
                }
                .width(60)
                TableColumn("Transcript", value: \.transcription.orEmpty)
            }
            .id(transmissionList.dataVersion)
        }
    }
}

struct TransmissionSearchBarView: View {
    @Binding var searchText: String
    let isEnabled: Bool

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)
            TextField(
                isEnabled ? "Search transmissions" : "Initializing search index…",
                text: $searchText,
            )
            .textFieldStyle(.roundedBorder)
            .disabled(!isEnabled)
        }
    }
}

struct TransmissionDetailsView: View {
    let transmission: Transmission?

    var body: some View {
        if let transmission {
            VStack(alignment: .leading, spacing: 4) {
                Text("Transmission Details:")
                    .font(.headline)
                Text("\(transmission.eventID) — \(transmission.startTime)")
                Text("\(transmission.station) on system \(transmission.system) channel \(transmission.channel)")
                Text(transmission.transcription.orEmpty)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        } else {
            Text("No transmission selected")
                .foregroundStyle(.secondary)
        }
    }
}

#Preview("Transmissions") {
    ContentView()
}
