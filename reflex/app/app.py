"""
Application
"""

from os import environ
from pathlib import Path

from twisted.logger import Logger

import app as appModule
from reflex import App
from transmissions.ext.click import readConfig
from transmissions.ext.logger import startLogging
from transmissions.run._store import storeFactoryFromConfig
from transmissions.store import TXDataStore


log = Logger()


class StoreFactory:
    """
    Factory for data store.
    """

    _store: TXDataStore = None

    async def store(self) -> TXDataStore | None:
        """
        Get and cache the data store.
        """
        if self._store is None:
            defaultConfigPath = Path("~/.rtx.toml")  # FIXME: Not DRY; see _command.py
            fileName = environ.get("CONFIG", defaultConfigPath)

            log.info("Reading configuration file: {file}", file=fileName)
            config = readConfig(Path(fileName))
            storeFactory = storeFactoryFromConfig(config, create=False)

            log.info("Initializing data store")
            self._store = await storeFactory()

        return self._store


appModule.storeFactory = StoreFactory()

startLogging()

app = App()
