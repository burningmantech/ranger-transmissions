from collections import deque
from collections.abc import Awaitable, Iterable
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import timezone as TimeZone
from enum import Enum
from hashlib import sha256
from os import walk
from pathlib import Path
from re import Pattern
from re import compile as regex
from time import sleep
from typing import TYPE_CHECKING, Any, ClassVar, cast

from attrs import frozen
from pydub import AudioSegment
from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread
from twisted.logger import Logger
from whisper import Whisper
from whisper import load_model as loadWhisper

from transmissions.ext.parallel import runInParallel
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
    _whisperUseFP16 = None

    @classmethod
    def whisper(cls) -> Whisper:
        """
        Build a Whisper model.
        """
        if cls._whisper is None:
            Indexer.log.info("Loading Whisper model...")

            if TYPE_CHECKING:
                device = "cpu"
            else:
                import torch

                if torch.cuda.is_available():
                    device = "cuda"
                    cls._whisperUseFP16 = True
                else:
                    device = "cpu"
                    cls._whisperUseFP16 = False

            cls._whisper = loadWhisper("large").to(device)

        return cls._whisper

    event: Event
    root: Path

    def _duration(self, path: Path) -> TimeDelta:
        audio = AudioSegment.from_wav(str(path))
        return TimeDelta(milliseconds=len(audio))

    def _sha256(self, path: Path) -> str:
        hasher = sha256()
        with path.open("rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _transcription(self, path: Path) -> str:
        result = self.whisper().transcribe(str(path), fp16=self._whisperUseFP16)
        return cast(str, result["text"])

    def _transmissionFromFile(self, path: Path) -> Transmission:
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
                path = Path(dirpath) / filename
                self.log.info("Found audio file: {path}", path=path)
                try:
                    yield self._transmissionFromFile(path)
                except InvalidFileError as e:
                    self.log.error("{error}", error=e)

    async def _addDuration(
        self,
        store: TXDataStore,
        transmission: Transmission,
    ) -> None:
        self.log.info(
            "Computing duration for {transmission}", transmission=transmission
        )
        duration = await deferToThread(self._duration, transmission.path)
        await store.setTransmissionDuration(
            eventID=transmission.eventID,
            system=transmission.system,
            channel=transmission.channel,
            startTime=transmission.startTime,
            duration=duration,
        )

    async def _addSignature(
        self,
        store: TXDataStore,
        transmission: Transmission,
    ) -> None:
        self.log.info(
            "Computing SHA256 for {transmission}", transmission=transmission
        )
        sha256 = await deferToThread(self._sha256, transmission.path)
        await store.setTransmissionSHA256(
            eventID=transmission.eventID,
            system=transmission.system,
            channel=transmission.channel,
            startTime=transmission.startTime,
            sha256=sha256,
        )

    async def _addTranscription(
        self,
        store: TXDataStore,
        transmission: Transmission,
    ) -> None:
        self.log.info(
            "Computing transcription for {transmission}",
            transmission=transmission,
        )
        transcription = await deferToThread(
            self._transcription, transmission.path
        )
        await store.setTransmissionTranscription(
            eventID=transmission.eventID,
            system=transmission.system,
            channel=transmission.channel,
            startTime=transmission.startTime,
            transcription=transcription,
        )

    async def _ensureTransmission(
        self,
        store: TXDataStore,
        transmission: Transmission,
        taskQueue: deque[Awaitable],
        *,
        computeChecksum: bool,
        computeTranscription: bool,
        computeDuration: bool,
    ) -> None:
        self.log.info("Ensuring {transmission}", transmission=transmission)
        existingTransmission = await store.transmission(
            eventID=transmission.eventID,
            system=transmission.system,
            channel=transmission.channel,
            startTime=transmission.startTime,
        )
        if existingTransmission is None:
            await store.createTransmission(transmission)
        else:
            # FIXME: If these don't match, we could clean up the DB
            assert transmission.station == existingTransmission.station
            assert transmission.path == existingTransmission.path
            transmission = existingTransmission

        if computeChecksum and transmission.sha256 is None:
            taskQueue.append(self._addSignature(store, transmission))

        if computeDuration and transmission.duration is None:
            taskQueue.append(self._addDuration(store, transmission))

        if computeTranscription and transmission.transcription is None:
            taskQueue.append(self._addTranscription(store, transmission))

    async def indexIntoStore(
        self,
        store: TXDataStore,
        *,
        computeChecksum: bool = True,
        computeTranscription: bool = True,
        computeDuration: bool = True,
    ) -> None:
        """
        Scans files contained within the root directory and adds them to the
        data store.
        Transcriptions will be lacking duration, SHA256 hash, and
        transcriptions, which must be computed later.
        """
        events = set(await store.events())

        if self.event not in events:
            await store.createEvent(self.event)

        taskQueue: deque[Awaitable[Any]] = deque()
        scanComplete = False

        def scan() -> None:
            nonlocal scanComplete
            for transmission in self.transmissions():
                # Note that the data store may not be thread safe but we are OK
                # here because we aren't doing the actual store work in the
                # scanning thread; we are merely adding it to a queue, which is
                # processed on the main thread.
                taskQueue.append(
                    self._ensureTransmission(
                        store,
                        transmission,
                        taskQueue,
                        computeChecksum=computeChecksum,
                        computeTranscription=computeTranscription,
                        computeDuration=computeDuration,
                    )
                )
            scanComplete = True

        scanTask = deferToThread(scan)

        if computeTranscription:
            # Load Whisper before we start tasks
            self.whisper()

        def tasks() -> Iterable[Deferred[Any]]:
            """
            Yields the next task to the parallel task runner.
            """
            while True:
                # yields tasks from the task queue.
                # We don't iterate over for queue in a for loop, because we are
                # altering it as we go.
                while taskQueue:
                    yield cast(Deferred[Any], taskQueue.pop())
                # The queue is empty, but don't break unless the scanning
                # thread is also done.
                if scanComplete:
                    break
                # The scanning thread is not done yet.
                # Sleep the main thread to let the scanning thread add more
                # tasks to the queue.
                sleep(0.01)

        await runInParallel(tasks(), maxTasks=32)

        assert scanComplete
        await scanTask
