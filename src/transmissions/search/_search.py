from collections.abc import AsyncIterable, Iterable
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar

from attrs import mutable
from twisted.logger import Logger
from whoosh.fields import DATETIME, ID, NUMERIC, TEXT, Schema
from whoosh.filedb.filestore import FileStorage, RamStorage
from whoosh.index import Index
from whoosh.qparser import QueryParser
from whoosh.writing import CLEAR, AsyncWriter

from transmissions.model import Transmission


__all__ = ()


class Location(Enum):
    memory = auto()


@mutable(kw_only=True)
class TransmissionsIndex:
    """
    Transmissions search index.
    """

    log: ClassVar[Logger] = Logger()

    schema: ClassVar[Schema] = Schema(
        eventID=ID(stored=True),
        station=ID(),
        system=ID(stored=True),
        channel=ID(stored=True),
        startTime=DATETIME(stored=True),
        duration=NUMERIC,
        path=ID,
        sha256=ID,
        transcription=TEXT,
    )

    _index: Index | None = None

    async def connect(self, location: Location | Path = Location.memory) -> None:
        """
        Connect to the index.
        """
        assert self._index is None

        indexname = "transmissions"

        if location is Location.memory:
            storage = RamStorage()
            self.log.info("Creating in-memory search index")
            index = storage.create_index(self.schema, indexname=indexname)
        else:
            storage = FileStorage(str(location))
            if location.exists():
                index = storage.open_index(indexname=indexname)
            else:
                self.log.info("Creating search index: {path}", path=location)
                location.mkdir()
                index = storage.create_index(self.schema, indexname=indexname)

        self._index = index

    async def add(self, transmissions: Iterable[Transmission]) -> None:
        """
        Add the given transmissions to the index.
        """
        assert self._index is not None

        writer = AsyncWriter(self._index)
        count = 0

        for transmission in transmissions:
            fields = {
                "eventID": transmission.eventID,
                "station": transmission.station,
                "system": transmission.system,
                "channel": transmission.channel,
                "startTime": transmission.startTime,
                "path": str(transmission.path),
            }
            if transmission.duration is not None:
                fields["duration"] = transmission.duration.total_seconds()
            if transmission.sha256 is not None:
                fields["sha256"] = transmission.sha256
            if transmission.transcription is not None:
                fields["transcription"] = transmission.transcription

            writer.add_document(**fields)

            count += 1

        # NOTE: AsyncWriter's commit is… not async, so there's apparently no
        # way to await on completion of the indexing thread here.
        writer.commit()

        self.log.info("Added {count} transmissions to search index", count=count)

    async def clear(self) -> None:
        """
        Clear all transmissions from the index.
        """
        assert self._index is not None

        writer = AsyncWriter(self._index)

        # NOTE: AsyncWriter's commit is… not async, so there's apparently no
        # way to await on completion of the indexing thread here.
        writer.commit(mergetype=CLEAR)

    async def search(
        self, queryText: str, limit: int | None = None
    ) -> AsyncIterable[Transmission.Key]:
        """
        Perform search.
        """
        assert self._index is not None

        parser = QueryParser("transcription", schema=self._index.schema)
        query = parser.parse(queryText)

        with self._index.searcher() as searcher:
            for result in searcher.search(query, limit=limit):
                yield (
                    result["eventID"],
                    result["system"],
                    result["channel"],
                    result["startTime"],
                )
