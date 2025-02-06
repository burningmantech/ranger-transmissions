from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from click import UsageError

from transmissions.store import TXDataStore


__all__ = ()


StoreFactory = Callable[[], Awaitable[TXDataStore]]


def storeFactoryFromConfig(
    configuration: dict[str, Any], *, create: bool = True
) -> StoreFactory:
    baseConfig = configuration.get("Store", {})
    storeType = baseConfig.get("Type", "SQLite")
    storeConfig = baseConfig.get(storeType, {})

    if storeType == "SQLite":
        return sqliteStoreFactoryFromConfig(storeConfig, create=create)

    raise UsageError("Unknown data store")


def sqliteStoreFactoryFromConfig(
    storeConfig: dict[str, Any], *, create: bool = True
) -> StoreFactory:
    from transmissions.store.sqlite import DataStore

    fileName = storeConfig.get("File", "~/rtx.sqlite")
    filePath = Path(fileName).expanduser()

    async def factory() -> TXDataStore:
        if not create and not filePath.exists():
            raise FileNotFoundError(fileName)

        store = DataStore(dbPath=filePath)
        await store.upgradeSchema()
        return store

    return factory
