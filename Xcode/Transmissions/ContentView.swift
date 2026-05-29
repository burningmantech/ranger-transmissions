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

    var body: some View {
        Table(transmissions) {
            TableColumn("Time", value: \.startTime.description)
            TableColumn("Event ID", value: \.eventID)
            TableColumn("Station", value: \.station)
            TableColumn("System", value: \.system)
            TableColumn("Channel", value: \.channel)
            TableColumn("Transcript", value: \.transcription.orEmpty)
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
