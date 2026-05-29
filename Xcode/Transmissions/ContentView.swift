//
//  ContentView.swift
//  Transmissions
//
//  Created by Wilfredo Sánchez Vega on 5/28/26.
//

import SwiftUI

extension Optional where Wrapped == String {
    var orEmpty: Wrapped {
        self ?? ""
    }
}

struct Transmission: Identifiable {
    let startTime: Date
    let eventID: String
    let station: String
    let system: String
    let channel: String
    let duration: TimeInterval?
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

    var body: some View {
        VStack {
            TransmissionSearchBarView(searchText: $searchText)
            TransmissionTableView(
                searchText: $searchText,
            )
            TransmissionDetailsView()
        }
        .padding()
    }
}

struct TransmissionTableView: View {
    @Binding var searchText: String

    @State private var sortOrder: [KeyPathComparator<Transmission>] = [
        KeyPathComparator(\.startTime)
    ]

    let transmissions: [Transmission] = [
        Transmission(
            startTime: Date(),
            eventID: "2024",
            station: "Tool",
            system: "A",
            channel: "Ranger HQ",
            duration: 0.0,
            path: "/",
            sha256: "",
            transcription: "Crow, Crow, Tool",
            transcriptionVersion: 0,
        ),
        Transmission(
            startTime: Date(),
            eventID: "2023",
            station: "Crow",
            system: "A",
            channel: "Ranger HQ",
            duration: 0.0,
            path: "/",
            sha256: "",
            transcription: "Tool, go for Crow",
            transcriptionVersion: 0,
        ),
        Transmission(
            startTime: Date(),
            eventID: "2021",
            station: "Tool",
            system: "A",
            channel: "Ranger HQ",
            duration: 0.0,
            path: "/",
            sha256: "",
            transcription: "Crow, are you available, and if so what's you 20?",
            transcriptionVersion: 0,
        ),
    ]

    var filteredTransmissions: [Transmission] {
        let sorted = transmissions.sorted(using: sortOrder)
        guard !searchText.isEmpty else { return sorted }
        return sorted.filter { transmission in
            transmission.eventID.localizedCaseInsensitiveContains(searchText)
                || transmission.station.localizedCaseInsensitiveContains(searchText)
                || transmission.system.localizedCaseInsensitiveContains(searchText)
                || transmission.channel.localizedCaseInsensitiveContains(searchText)
                || transmission.transcription.orEmpty.localizedCaseInsensitiveContains(searchText)
        }
    }

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "EE MM/dd HH:mm"
        return formatter
    }()

    var body: some View {
        VStack {
            Table(filteredTransmissions, sortOrder: $sortOrder) {
                TableColumn("Event ID", value: \.eventID)
                TableColumn("Time", value: \.startTime) { transmission in
                    Text(dateFormatter.string(from: transmission.startTime))
                }
                TableColumn("Station", value: \.station)
                TableColumn("System", value: \.system)
                TableColumn("Channel", value: \.channel)
                TableColumn("Transcript", value: \.transcription.orEmpty)
            }
        }
    }
}

struct TransmissionSearchBarView: View {
    @Binding var searchText: String

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)
            TextField("Search transmissions", text: $searchText)
                .textFieldStyle(.roundedBorder)
        }
    }
}

struct TransmissionDetailsView: View {
    var body: some View {
        Text("Transmission Details")
    }
}

#Preview("Transmissions") {
    ContentView()
}
