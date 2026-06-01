//
//  TransmissionDatabase.swift
//  Transmissions
//

import Foundation
import SQLite3

enum TransmissionDatabaseError: Error {
    case openFailed(String)
    case prepareFailed(String)
}

struct TransmissionDatabase {
    let url: URL

    func loadTransmissions() throws -> [Transmission] {
        var db: OpaquePointer?
        guard sqlite3_open_v2(url.path, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK else {
            let message = db.map { String(cString: sqlite3_errmsg($0)) } ?? "unknown error"
            sqlite3_close(db)
            throw TransmissionDatabaseError.openFailed(message)
        }
        defer { sqlite3_close(db) }

        let sql = """
            SELECT EVENT, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
                   FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
            FROM TRANSMISSION
            """

        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK else {
            let message = String(cString: sqlite3_errmsg(db))
            throw TransmissionDatabaseError.prepareFailed(message)
        }
        defer { sqlite3_finalize(statement) }

        var results: [Transmission] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            results.append(
                Transmission(
                    eventID: columnText(statement, 0) ?? "",
                    station: columnText(statement, 1) ?? "",
                    system: columnText(statement, 2) ?? "",
                    channel: columnText(statement, 3) ?? "",
                    startTime: Date(timeIntervalSince1970: sqlite3_column_double(statement, 4)),
                    duration: columnDouble(statement, 5).map { Duration.seconds($0) },
                    path: columnText(statement, 6) ?? "",
                    sha256: columnText(statement, 7),
                    transcription: columnText(statement, 8),
                    transcriptionVersion: columnInt(statement, 9),
                )
            )
        }

        return results
    }

    private func columnText(_ statement: OpaquePointer?, _ index: Int32) -> String? {
        guard let cString = sqlite3_column_text(statement, index) else { return nil }
        return String(cString: cString)
    }

    private func columnDouble(_ statement: OpaquePointer?, _ index: Int32) -> Double? {
        guard sqlite3_column_type(statement, index) != SQLITE_NULL else { return nil }
        return sqlite3_column_double(statement, index)
    }

    private func columnInt(_ statement: OpaquePointer?, _ index: Int32) -> Int? {
        guard sqlite3_column_type(statement, index) != SQLITE_NULL else { return nil }
        return Int(sqlite3_column_int64(statement, index))
    }
}
