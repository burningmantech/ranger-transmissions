"""
Application
"""

from os import environ
from pathlib import Path

from reflex import App
from twisted.logger import Logger

from transmissions.ext.click import readConfig
from transmissions.ext.logger import startLogging
from transmissions.run._search import searchIndexFactoryFromConfig  # FIXME: private
from transmissions.run._store import storeFactoryFromConfig  # FIXME: private
from transmissions.search import TransmissionsIndex
from transmissions.store import TXDataStore


log = Logger()


class StoreFactory:
    """
    Factory for data store.
    """

    _store: TXDataStore | None = None

    async def store(self) -> TXDataStore:
        """
        Get and cache the data store.
        """
        if self._store is None:
            log.info("Initializing data store...")
            storeFactory = storeFactoryFromConfig(configuration, create=False)
            self._store = await storeFactory()

        return self._store


class SearchIndexFactory:
    """
    Factory for search index.
    """

    _index: TransmissionsIndex | None = None

    async def index(self, store: TXDataStore) -> TransmissionsIndex:
        """
        Get and cache the search index.
        """
        if self._index is None:
            log.info("Initializing search index...")
            searchIndexFactory = searchIndexFactoryFromConfig(configuration)
            self._index = await searchIndexFactory(store)

        return self._index


startLogging()

defaultConfigPath = Path("~/.rtx.toml")  # FIXME: Not DRY; see _command.py
fileName = environ.get("CONFIG", defaultConfigPath)

log.info("Reading configuration file: {file}", file=fileName)
configuration = readConfig(Path(fileName))

storeFactory = StoreFactory()
searchIndexFactory = SearchIndexFactory()

app = App()
