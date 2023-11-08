from collections.abc import AsyncIterable, Iterable
from enum import Enum, auto
from typing import ClassVar

from attrs import mutable
from whoosh.fields import DATETIME, ID, NUMERIC, TEXT, Schema
from whoosh.filedb.filestore import RamStorage
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

    async def connect(self, location: Location = Location.memory) -> None:
        """
        Connect to the index.
        """
        assert location is Location.memory
        assert self._index is None

        storage = RamStorage()
        self._index = storage.create_index(self.schema)

    async def add(self, transmissions: Iterable[Transmission]) -> None:
        """
        Add the given transmissions to the index.
        """
        assert self._index is not None

        writer = AsyncWriter(self._index)

        for transmission in transmissions:
            fields = dict(
                eventID=transmission.eventID,
                station=transmission.station,
                system=transmission.system,
                channel=transmission.channel,
                startTime=transmission.startTime,
                path=str(transmission.path),
            )
            if transmission.duration is not None:
                fields["duration"] = transmission.duration.total_seconds()
            if transmission.sha256 is not None:
                fields["sha256"] = transmission.sha256
            if transmission.transcription is not None:
                fields["transcription"] = transmission.transcription

            writer.add_document(**fields)

        # NOTE: AsyncWriter's commit is… not async, so there's apparently no
        # way to await on completion of the indexing thread here.
        writer.commit()

    async def clear(self) -> None:
        """
        Clear all transmissions from the index.
        """
        assert self._index is not None

        writer = AsyncWriter(self._index)

        # NOTE: AsyncWriter's commit is… not async, so there's apparently no
        # way to await on completion of the indexing thread here.
        writer.commit(mergetype=CLEAR)

    async def search(self, queryText: str) -> AsyncIterable[Transmission.Key]:
        """
        Perform search.
        """
        assert self._index is not None

        parser = QueryParser("transcription", schema=self._index.schema)
        query = parser.parse(queryText)

        with self._index.searcher() as searcher:
            for result in searcher.search(query, limit=None):
                result.fields()
                yield (
                    result["eventID"],
                    result["system"],
                    result["channel"],
                    result["startTime"],
                )
