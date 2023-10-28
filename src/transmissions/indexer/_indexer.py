from collections.abc import Iterable
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from enum import Enum
from hashlib import sha256
from os import walk
from pathlib import Path
from re import Pattern
from re import compile as regex
from typing import ClassVar

from attrs import frozen
from pydub import AudioSegment
from twisted.logger import Logger
from whisper import Whisper
from whisper import load_model as loadWhisper

from transmissions.model import Event, Transmission
from transmissions.store import TXDataStore


__all__ = ()


class TZInfo(Enum):
    """
    Time zones
    """

    PDT = TimeZone(TimeDelta(hours=-7), name="Pacific Daylight Time")


class InvalidFileError(Exception):
    """
    Don't like this file, yo.
    """


class Patterns:
    """
    Regex patterns.
    """

    _pattern_2017: Pattern[str] | None = None
    _pattern_2023: Pattern[str] | None = None

    @classmethod
    def pattern_2017(cls) -> Pattern:
        """
        Regex for 2017 file names.
        """
        # Examples:
        "2017-08-28 21-40-52 SYSTEM A Radio _MDC_"
        "calls group _ESD Ops 1_ (00-04).wav"

        "2017-09-01 00-01-09 SYSTEM A Radio _RANGERS # 6526_ "
        "calls group _BRC 911_ (00-02).wav"

        "2017-08-28 20-41-03 SYSTEM A Dispatcher _Administrator_ "
        "calls group _ESD Ops 1_ (00-06).wav"

        "2017-08-21 14-15-27 Intercom Intercom Call- Dispatcher "
        "_Administrator_ calls all dispatchers (00-05).wav"

        "2017-08-29 17-31-23 Trunk Sys B Radio _RANGERS # 6335_ "
        "calls group _Control 1_.wav"

        if cls._pattern_2017 is None:
            cls._pattern_2017 = regex(
                r"^"
                r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
                r" (?P<hour>\d{2})-(?P<minute>\d{2})-(?P<second>\d{2})"
                r" (?P<systemType>Trunk Sys|\w+)"
                r" (?P<systemName>\w+)"
                r"(| Call-)"
                r" (?P<stationType>\w*)"
                r" _(?P<stationName>.+)_"
                r" calls(| group)"
                r" (_(?P<channel1>[^_]+)_|(?P<channel2>all dispatchers))"
                r"( \((?P<minutes>\d{2})-(?P<seconds>\d{2})\))?"
                r".*"
                r"\.wav$"
            )
        return cls._pattern_2017

    @classmethod
    def pattern_2023(cls) -> Pattern:
        """
        Regex for 2023 file names.
        """
        # Examples:
        "2023-08-24 18-28-05 SYSTEM A Group Call- 'Ranger Evnt 148' called"
        "'RANGER TAC 1'.wav"

        "2023-09-04 20-13-56 SYSTEM A Group Call- 'Ranger Shift 57' called "
        "'RANGER TAC 1'.wav"

        "2023-09-04 22-55-55 SYSTEM A Group Call- 'RNGRS DPW-STE 04' called "
        "'RANGER TAC 1'.wav"

        "2023-09-04 13-24-02 SYSTEM A Group Call- 'gpe 650-85' called "
        "'PERIMETER'.wav"

        "2023-08-28 22-39-27 SYSTEM B Group Call- 'Ranger Com 29' called "
        "'CONTROL 1'.wav"

        "2023-09-02 19-59-03 SYSTEM A Group Call- 'Engine 3-A' called "
        "'ESD OPS1'.wav"

        "2023-09-02 04-07-07 SYSTEM A Group Call- 'Delta Boss A' called "
        "'ESD OPS1'.wav"

        "2023-09-02 23-47-48 SYSTEM B Group Call- 'Burn 30' called "
        "'ESD OPS 2'.wav"

        "2023-08-26 09-07-04 SYSTEM A Group Call- 'BLM Gateway 02' called "
        "'BLM IR-17'.wav"

        if cls._pattern_2023 is None:
            cls._pattern_2023 = regex(
                r"^"
                r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
                r" (?P<hour>\d{2})-(?P<minute>\d{2})-(?P<second>\d{2})"
                r" SYSTEM (?P<systemName>[AB]) Group Call-"
                r" '(?P<stationName>[^']+)' called '(?P<channel1>[^']+)'"
                r".*"
                r"\.wav$"
            )
        return cls._pattern_2023


@frozen(kw_only=True)
class Indexer:
    """
    Radio Transmission Indexer
    """

    log: ClassVar[Logger] = Logger()

    _whisper: ClassVar[Whisper] = None

    @classmethod
    def whisper(cls) -> Whisper:
        """
        Build a Whisper model.
        """
        if cls._whisper is None:
            Indexer.log.info("Loading Whisper model...")
            cls._whisper = loadWhisper("medium.en")
        return cls._whisper

    event: Event
    root: Path

    def _transmissionFromFile(
        self, path: Path, _expensiveParts: bool = False
    ) -> Transmission:
        """
        Returns a Transmission based on the given Path to a file.
        """
        match = Patterns.pattern_2023().match(path.name)

        if match is None:
            raise InvalidFileError(f"Skipping file {path}")

        # Start time

        startTime = DateTime(
            year=int(match.group("year")),
            month=int(match.group("month")),
            day=int(match.group("day")),
            hour=int(match.group("hour")),
            minute=int(match.group("minute")),
            second=int(match.group("second")),
            tzinfo=TZInfo.PDT.value,
        )

        # System

        systemName = match.group("systemName")
        try:
            systemType = match.group("systemType")
        except IndexError:
            system = f"System {systemName}"
        else:
            systemType = {
                "SYSTEM": "Conventional",
                "Trunk Sys": "Trunk",
            }.get(systemType, systemType)

            if systemType == systemName:
                system = systemName
            else:
                system = f"{systemType} {systemName}"

        # Station

        stationName = match.group("stationName")
        try:
            stationType = match.group("stationType")
        except IndexError:
            station = stationName
        else:
            station = f"{stationType} {stationName}"

        # Channel

        try:
            channel = match.group("channel1")
        except IndexError:
            channel = match.group("channel2")

        if _expensiveParts:
            # Duration

            audio = AudioSegment.from_wav(str(path))
            duration = TimeDelta(milliseconds=len(audio))

            # Checksum

            hasher = sha256()
            with path.open("rb") as f:
                hasher.update(f.read())
            sha256Digest = hasher.hexdigest()

            # Speech -> text
            transcription = self.whisper().transcribe(str(path))

        else:
            duration = None
            sha256Digest = None
            transcription = None

        # Return result

        return Transmission(
            eventID=self.event.id,
            station=station,
            system=system,
            channel=channel,
            startTime=startTime,
            duration=duration,
            path=path,
            sha256=sha256Digest,
            transcription=transcription,
        )

    def transmissions(self) -> Iterable[Transmission]:
        """
        Returns an Iterable of Transmissions based on files contained within
        the root directory.
        """
        for (
            dirpath,
            dirnames,
            filenames,
        ) in walk(self.root):
            self.log.info(
                "Scanning directory: {dirpath}",
                dirpath=dirpath,
                dirnames=dirnames,
                filenames=len(filenames),
            )
            for filename in filenames:
                try:
                    yield self._transmissionFromFile(Path(dirpath) / filename)
                except InvalidFileError as e:
                    self.log.error("{error}", error=e)

    async def indexIntoStore(self, store: TXDataStore) -> None:
        """
        Scans files contained within the root directory and adds them to the
        data store.
        """
        events = set(await store.events())

        if self.event not in events:
            await store.createEvent(self.event)

        for transmission in self.transmissions():
            self.log.info(
                "Indexing transmission: {transmission}",
                transmission=transmission,
            )
