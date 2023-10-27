from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from click import UsageError

from transmissions.store import TXDataStore


__all__ = ()


StoreFactory = Callable[[], Awaitable[TXDataStore]]


def storeFactoryFromConfig(configuration: dict[str, Any]) -> StoreFactory:
    baseConfig = configuration.get("Store", {})
    storeType = baseConfig.get("Type", "SQLite")
    storeConfig = baseConfig.get(storeType, {})

    if storeType == "SQLite":
        return sqliteStoreFactoryFromConfig(storeConfig)

    raise UsageError("Unknown data store")


def sqliteStoreFactoryFromConfig(storeConfig: dict[str, Any]) -> StoreFactory:
    from transmissions.store.sqlite import DataStore

    fileName = storeConfig.get("File", "./rtx.toml")

    async def factory() -> TXDataStore:
        store = DataStore(dbPath=Path(fileName))
        await store.upgradeSchema()
        return store

    return factory
