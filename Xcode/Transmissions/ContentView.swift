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

    let transmissions: [Transmission] = [
        Transmission(
            startTime: Date(),
            eventID: "2024",
            station: "Tool",
            system: "A",
            channel: "Ranger HQ",
            duration: Duration.seconds(0.0),
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
            duration: Duration.seconds(2.0),
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
            duration: nil,
            path: "/",
            sha256: "",
            transcription: "Crow, are you available, and if so what's you 20?",
            transcriptionVersion: 0,
        ),
    ]

    var selectedTransmission: Transmission? {
        guard let selectedTransmissionID else { return nil }
        return transmissions.first { $0.id == selectedTransmissionID }
    }

    var body: some View {
        VStack {
            TransmissionSearchBarView(searchText: $searchText)
            TransmissionTableView(
                transmissions: transmissions,
                searchText: $searchText,
                selectedTransmissionID: $selectedTransmissionID,
            )
            TransmissionDetailsView(transmission: selectedTransmission)
        }
        .padding()
    }
}

struct TransmissionTableView: View {
    let transmissions: [Transmission]

    @Binding var searchText: String
    @Binding var selectedTransmissionID: Transmission.ID?

    @State private var sortOrder: [KeyPathComparator<Transmission>] = [
        KeyPathComparator(\.startTime)
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

    private let durationStyle = Duration.TimeFormatStyle(pattern: .hourMinuteSecond(padHourToLength: 2))

    var body: some View {
        VStack {
            Table(filteredTransmissions, selection: $selectedTransmissionID, sortOrder: $sortOrder) {
                TableColumn("Event ID", value: \.eventID)
                TableColumn("Station", value: \.station)
                TableColumn("System", value: \.system)
                TableColumn("Time", value: \.startTime) { transmission in
                    Text(dateFormatter.string(from: transmission.startTime))
                }
                TableColumn("Channel", value: \.channel)
                TableColumn("Duration", value: \.duration.orZero) { transmission in
                    Text(transmission.duration?.formatted(durationStyle) ?? "")
                }
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
