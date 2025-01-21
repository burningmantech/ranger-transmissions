from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from transmissions.search import Location, TransmissionsIndex
from transmissions.store import TXDataStore
from transmissions.store.sqlite import DataStore as SQLiteDataStore


__all__ = ()


SearchIndexFactory = Callable[[TXDataStore], Awaitable[TransmissionsIndex]]


def searchIndexFactoryFromConfig(configuration: dict[str, Any]) -> SearchIndexFactory:
    searchConfig = configuration.get("SearchIndex", {})
    fileName = searchConfig.get("File", "~/rtx.whoosh_index")

    async def factory(store: TXDataStore) -> TransmissionsIndex:
        reindex = True

        if fileName:
            indexPath = Path(fileName).expanduser()
            if isinstance(store, SQLiteDataStore):
                if (
                    indexPath.is_dir()
                    and store.dbPath is not None
                    and indexPath.stat().st_mtime > store.dbPath.stat().st_mtime
                ):
                    reindex = False
            else:
                raise NotImplementedError("Don't know whether to reindex")
            location: Location | Path = indexPath
        else:
            location = Location.memory

        index = TransmissionsIndex()
        await index.connect(location=location)

        if reindex:
            await index.add(await store.transmissions())

        return index

    return factory
