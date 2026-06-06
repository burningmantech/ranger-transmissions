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

nonisolated private let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

nonisolated final class TransmissionDatabase: @unchecked Sendable {
    private var db: OpaquePointer?

    init(url: URL) throws {
        var handle: OpaquePointer?
        let flags = SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX
        let result = sqlite3_open_v2(url.path, &handle, flags, nil)
        guard result == SQLITE_OK else {
            let message = handle.map { String(cString: sqlite3_errmsg($0)) } ?? "unknown error"
            sqlite3_close(handle)
            throw TransmissionDatabaseError.openFailed(message)
        }
        self.db = handle
        // Keep the temp FTS index in RAM so queries don't pay disk I/O.
        try execute("PRAGMA temp_store = MEMORY")
    }

    deinit {
        sqlite3_close(db)
    }

    func count() throws -> Int {
        let sql = "select count(*) from TRANSMISSION"
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK else {
            throw TransmissionDatabaseError.prepareFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(statement) }
        guard sqlite3_step(statement) == SQLITE_ROW else { return 0 }
        return Int(sqlite3_column_int64(statement, 0))
    }

    func transmissions(
        orderBy: String,
        offset: Int,
        limit: Int,
    ) throws -> [Transmission] {
        let sql = """
            select EVENT as EVENT_ID, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
                   FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
            from TRANSMISSION \(orderBy) LIMIT ? OFFSET ?
            """
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK else {
            throw TransmissionDatabaseError.prepareFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(statement) }
        sqlite3_bind_int64(statement, 1, sqlite3_int64(limit))
        sqlite3_bind_int64(statement, 2, sqlite3_int64(offset))
        var results: [Transmission] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            results.append(makeTransmission(from: statement))
        }
        return results
    }

    func count(matching searchText: String) throws -> Int {
        let trimmed = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        let useMatch = !trimmed.isEmpty
        let baseSelect = "select count(*) from TRANSMISSIONS_FTS"
        let whereClause = useMatch ? " where TRANSMISSIONS_FTS match ?" : ""
        let sql = "\(baseSelect)\(whereClause)"

        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK else {
            throw TransmissionDatabaseError.prepareFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(statement) }

        if useMatch {
            sqlite3_bind_text(statement, 1, fts5Query(for: trimmed), -1, SQLITE_TRANSIENT)
        }

        guard sqlite3_step(statement) == SQLITE_ROW else { return 0 }
        return Int(sqlite3_column_int64(statement, 0))
    }

    func transmissions(
        matching searchText: String,
        orderBy: String,
        offset: Int,
        limit: Int,
    ) throws -> [Transmission] {
        let trimmed = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        let useMatch = !trimmed.isEmpty

        let baseSelect = """
            select EVENT_ID, STATION, SYSTEM, CHANNEL, START_TIME, DURATION,
                   FILE_NAME, SHA256, TRANSCRIPTION, TRANSCRIPTION_VERSION
            from TRANSMISSIONS_FTS
            """
        let whereClause = useMatch ? " where TRANSMISSIONS_FTS match ?" : ""
        let sql = "\(baseSelect)\(whereClause) \(orderBy) LIMIT ? OFFSET ?"

        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK else {
            throw TransmissionDatabaseError.prepareFailed(String(cString: sqlite3_errmsg(db)))
        }
        defer { sqlite3_finalize(statement) }

        var bindIndex: Int32 = 1
        if useMatch {
            sqlite3_bind_text(statement, bindIndex, fts5Query(for: trimmed), -1, SQLITE_TRANSIENT)
            bindIndex += 1
        }
        sqlite3_bind_int64(statement, bindIndex, sqlite3_int64(limit))
        sqlite3_bind_int64(statement, bindIndex + 1, sqlite3_int64(offset))

        var results: [Transmission] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            results.append(makeTransmission(from: statement))
        }
        return results
    }

    func buildFullTextIndex() throws {
        try execute("""
            create virtual table temp.TRANSMISSIONS_FTS using fts5(
                EVENT_ID, STATION, SYSTEM, CHANNEL, TRANSCRIPTION,
                START_TIME unindexed,
                DURATION unindexed,
                FILE_NAME unindexed,
                SHA256 unindexed,
                TRANSCRIPTION_VERSION unindexed
            )
            """)
        try execute("""
            insert into temp.TRANSMISSIONS_FTS (
                EVENT_ID, STATION, SYSTEM, CHANNEL, TRANSCRIPTION,
                START_TIME, DURATION, FILE_NAME, SHA256, TRANSCRIPTION_VERSION
            )
            select EVENT, STATION, SYSTEM, CHANNEL, TRANSCRIPTION,
                   START_TIME, DURATION, FILE_NAME, SHA256, TRANSCRIPTION_VERSION
            from TRANSMISSION
            """)
        // Merge the index segments produced by the bulk insert so the very
        // first query doesn't pay the segment-traversal cost.
        try execute("""
            insert into temp.TRANSMISSIONS_FTS(TRANSMISSIONS_FTS) values('optimize')
            """)
        // Run a query that mirrors what a real search does (match + sort by
        // START_TIME) so SQLite materializes everything before we declare
        // the index "ready".
        try execute("""
            select count(*) from (
                select rowid from temp.TRANSMISSIONS_FTS
                where temp.TRANSMISSIONS_FTS match 'a*'
                order by START_TIME asc
                limit 1000
            )
            """)
    }

    private func execute(_ sql: String) throws {
        var errorPointer: UnsafeMutablePointer<CChar>?
        guard sqlite3_exec(db, sql, nil, nil, &errorPointer) == SQLITE_OK else {
            let message = errorPointer.map { String(cString: $0) } ?? "unknown error"
            sqlite3_free(errorPointer)
            throw TransmissionDatabaseError.prepareFailed(message)
        }
    }

    private func fts5Query(for text: String) -> String {
        text.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }
            .map { token in
                let escaped = token.replacingOccurrences(of: "\"", with: "\"\"")
                return "\"\(escaped)\"*"
            }
            .joined(separator: " ")
    }

    private func makeTransmission(from statement: OpaquePointer?) -> Transmission {
        Transmission(
            startTime: Date(timeIntervalSince1970: sqlite3_column_double(statement, 4)),
            eventID: columnText(statement, 0) ?? "",
            station: columnText(statement, 1) ?? "",
            system: columnText(statement, 2) ?? "",
            channel: columnText(statement, 3) ?? "",
            duration: columnDouble(statement, 5).map { Duration.seconds($0) },
            path: columnText(statement, 6) ?? "",
            sha256: columnText(statement, 7),
            transcription: columnText(statement, 8),
            transcriptionVersion: columnInt(statement, 9),
        )
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
