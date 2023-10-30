##
# See the file COPYRIGHT for copyright information.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

"""
Transmissions database tooling.
"""

from abc import abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from pathlib import Path
from textwrap import dedent
from typing import Any, ClassVar, Optional, TypeVar, Union, cast

from attrs import field, frozen
from twisted.logger import Logger

from transmissions.model import Event, Transmission

from ._abc import TXDataStore
from ._exceptions import StorageError


__all__ = ()


ParameterValue = Optional[Union[bytes, str, int, float]]
Parameters = Mapping[str, ParameterValue]


Row = Parameters
Rows = Iterator[Row]

T = TypeVar("T")


@frozen
class Query:
    description: str
    text: str = field(converter=dedent)


@frozen(kw_only=True)
class Queries:
    schemaVersion: Query
    events: Query
    createEvent: Query
    createEventOrIgnore: Query
    transmissions: Query
    transmission: Query
    createTransmission: Query


@frozen(kw_only=True)
class Transaction:
    lastrowid: int

    @abstractmethod
    def execute(self, sql: str, parameters: Parameters | None = None) -> None:
        """
        Executes an SQL statement.
        """

    @abstractmethod
    def executescript(self, sql_script: str) -> None:
        """
        Execute multiple SQL statements at once.
        """

    @abstractmethod
    def fetchone(self) -> Row | None:
        """
        Fetch the next row.
        """

    @abstractmethod
    def fetchall(self) -> Rows:
        """
        Fetch all rows.
        """


@frozen(kw_only=True)
class DatabaseStore(TXDataStore):
    """
    Incident Management System data store using a managed database.
    """

    log: ClassVar[Logger] = Logger()

    schemaVersion: ClassVar[int]
    schemaBasePath: ClassVar[Path]
    sqlFileExtension: ClassVar[str]

    query: ClassVar[Queries]

    @staticmethod
    def asDateTimeValue(dateTime: DateTime) -> ParameterValue:
        """
        Convert a :class:`DateTime` to a date-time value for the database.
        This implementation returns a :class:`float`.
        """
        assert dateTime.tzinfo is not None, repr(dateTime)
        timeStamp = dateTime.timestamp()
        if timeStamp < 0:
            raise StorageError(f"DateTime is before the UTC epoch: {dateTime}")
        return timeStamp

    @staticmethod
    def fromDateTimeValue(value: ParameterValue) -> DateTime:
        """
        Convert a date-time value from the database to a :class:`DateTime`.
        This implementation requires :obj:`value` to be a :class:`float`.
        """
        if not isinstance(value, float):
            raise TypeError("Time stamp in SQLite store must be a float")

        return DateTime.fromtimestamp(value, tz=TimeZone.utc)

    @staticmethod
    def asDurationValue(duration: TimeDelta) -> ParameterValue:
        """
        Convert a :class:`Duration` to a duration value for the database.
        This implementation returns a :class:`float`.
        """
        return duration.total_seconds()

    @staticmethod
    def fromDurationValue(value: ParameterValue) -> TimeDelta:
        """
        Convert a duration value from the database to a :class:`TimeDelta`.
        This implementation requires :obj:`value` to be a :class:`float`.
        """
        if not isinstance(value, float):
            raise TypeError("Duration in SQLite store must be a float")

        return TimeDelta(seconds=value)

    @classmethod
    def loadSchema(cls, version: int | str | None = None) -> str:
        """
        Read the schema file with the given version name.
        """
        if version is None:
            version = cls.schemaVersion

        name = f"{version}.{cls.sqlFileExtension}"
        path = cls.schemaBasePath / name
        return path.read_text()

    @property
    def dbManager(self) -> "DatabaseManager":
        return DatabaseManager(store=self)

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close any existing connections to the database.
        """

    async def close(self) -> None:
        await self.disconnect()

    @abstractmethod
    async def runQuery(
        self, query: Query, parameters: Parameters | None = None
    ) -> Rows:
        """
        Execute the given query with the given parameters, returning the
        resulting rows.
        """

    @abstractmethod
    async def runOperation(
        self, query: Query, parameters: Parameters | None = None
    ) -> None:
        """
        Execute the given query with the given parameters.
        """

    @abstractmethod
    async def runInteraction(
        self,
        interaction: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Create a transaction and call the given interaction with the
        transaction as the sole argument.
        """

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit.
        """

    @abstractmethod
    async def dbSchemaVersion(self) -> int:
        """
        The database's current schema version.
        """

    @abstractmethod
    async def applySchema(self, sql: str) -> None:
        """
        Apply the given schema to the database.
        """

    async def upgradeSchema(self, targetVersion: int | None = None) -> None:
        if await self.dbManager.upgradeSchema(targetVersion):
            await self.disconnect()

    async def validate(self) -> None:
        self.log.info("Validating data store...")

    ###
    # Events
    ###

    async def events(self) -> Iterable[Event]:
        return (
            Event(id=cast(str, row["ID"]), name=cast(str, row["NAME"]))
            for row in await self.runQuery(self.query.events)
        )

    async def createEvent(self, event: Event) -> None:
        await self.runOperation(
            self.query.createEvent, dict(eventID=event.id, eventName=event.name)
        )
        await self.commit()

        self.log.info(
            "Created event: {event}",
            storeWriteClass=Event,
            event=event,
        )

    ###
    # Transmissions
    ###

    async def transmissions(self) -> Iterable[Transmission]:
        raise NotImplementedError()

    async def transmission(
        self, eventID: str, system: str, channel: str, startTime: DateTime
    ) -> Transmission | None:
        found = False

        for row in await self.runQuery(
            self.query.transmission,
            dict(
                eventID=eventID,
                system=system,
                channel=channel,
                startTime=self.asDateTimeValue(startTime),
            ),
        ):
            assert found is not True
            found = True

            if row["DURATION"] is None:
                duration = None
            else:
                duration = self.fromDurationValue(cast(float, row["DURATION"]))

            return Transmission(
                eventID=cast(str, row["EVENT"]),
                station=cast(str, row["STATION"]),
                system=cast(str, row["SYSTEM"]),
                channel=cast(str, row["CHANNEL"]),
                startTime=self.fromDateTimeValue(
                    cast(float, row["START_TIME"])
                ),
                duration=duration,
                path=Path(cast(str, row["FILE_NAME"])),
                sha256=cast(str, row["SHA256"]),
                transcription=cast(str, row["TRANSCRIPTION"]),
            )

        return None

    async def createTransmission(self, transmission: Transmission) -> None:
        if transmission.duration is None:
            duration = None
        else:
            duration = self.asDurationValue(transmission.duration)

        await self.runOperation(
            self.query.createTransmission,
            dict(
                eventID=transmission.eventID,
                station=transmission.station,
                system=transmission.system,
                channel=transmission.channel,
                startTime=self.asDateTimeValue(transmission.startTime),
                duration=duration,
                fileName=str(transmission.path),
                sha256=transmission.sha256,
                transcription=transmission.transcription,
            ),
        )
        await self.commit()

        self.log.info(
            "Created transmission: {transmission}",
            storeWriteClass=Transmission,
            transmission=transmission,
        )


@frozen(kw_only=True)
class DatabaseManager:
    """
    Generic manager for databases.
    """

    log: ClassVar[Logger] = Logger()

    store: DatabaseStore

    async def upgradeSchema(self, targetVersion: int | None = None) -> bool:
        """
        Apply schema updates
        """
        if targetVersion is None:
            latestVersion = self.store.schemaVersion
        else:
            latestVersion = targetVersion

        currentVersion = await self.store.dbSchemaVersion()

        if currentVersion < 0:
            raise StorageError(
                f"No upgrade path from schema version {currentVersion}"
            )

        if currentVersion == latestVersion:
            # No upgrade needed
            self.log.debug(
                "No upgrade required for schema version {version}",
                version=currentVersion,
            )
            return False

        if currentVersion > latestVersion:
            raise StorageError(
                f"Schema version {currentVersion} is too new "
                f"(latest version is {latestVersion})"
            )

        async def sqlUpgrade(fromVersion: int, toVersion: int) -> None:
            self.log.info(
                "Upgrading database schema from version {fromVersion} to "
                "version {toVersion}",
                fromVersion=fromVersion,
                toVersion=toVersion,
            )

            if fromVersion == 0:
                fileID = f"{toVersion}"
            else:
                fileID = f"{toVersion}-from-{fromVersion}"

            try:
                try:
                    sql = self.store.loadSchema(version=fileID)
                except FileNotFoundError as e:
                    self.log.critical(
                        "Unable to upgrade schema in store {store.__class__} "
                        "from {fromVersion} to {toVersion} "
                        "due to missing schema upgrade file",
                        store=self.store,
                        fromVersion=fromVersion,
                        toVersion=toVersion,
                    )
                    raise StorageError("schema upgrade file not found") from e
                await self.store.applySchema(sql)
            except StorageError as e:
                raise StorageError(
                    f"Unable to upgrade schema from "
                    f"{fromVersion} to {toVersion}: {e}"
                ) from e

        fromVersion = currentVersion

        while fromVersion < latestVersion:
            if fromVersion == 0:
                toVersion = latestVersion
            else:
                toVersion = fromVersion + 1

            await sqlUpgrade(fromVersion, toVersion)
            fromVersion = await self.store.dbSchemaVersion()

            # Make sure the schema version increased from last version
            if fromVersion <= currentVersion:
                raise StorageError(
                    f"Schema upgrade did not increase schema version "
                    f"({fromVersion} <= {currentVersion})"
                )
            currentVersion = fromVersion

        return True
