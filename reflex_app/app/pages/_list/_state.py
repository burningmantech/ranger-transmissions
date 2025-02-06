"""
Transmissions List Page State
"""

from base64 import b64encode
from collections.abc import Mapping
from datetime import datetime as DateTime
from pathlib import Path
from typing import Any

from reflex import State as BaseState
from reflex import event, var
from twisted.logger import Logger

import app as Global
from app.model import RXTransmission
from transmissions.model import Transmission, TZInfo
from transmissions.search import TransmissionsIndex


log = Logger()

htmlLocalDateTimeFormat = "%Y-%m-%dT%H:%M"


def dataURLFromPath(path: Path, *, mimeType: str) -> str:
    with path.open("rb") as f:
        data = f.read()
    b64Text = b64encode(data).decode("utf-8")
    return f"data:{mimeType};base64,{b64Text}"


def dateTimeFromText(text: str, format: str) -> DateTime | None:
    if not text:
        return None
    return DateTime.strptime(text, format).replace(tzinfo=TZInfo.PDT.value)


def dateTimeFromHTMLLocalDateTimeText(text: str) -> DateTime | None:
    return dateTimeFromText(text, htmlLocalDateTimeFormat)


def htmlLocalDateTimeTextFromDateTime(dateTime: DateTime | None) -> str:
    if dateTime is None:
        return ""
    return dateTime.strftime(htmlLocalDateTimeFormat)


class State(BaseState):
    """
    Transmissions List Page State
    """

    _events: list[str] | None = None
    _selectedEvent: str | None = None
    _transmissions: Mapping[Transmission.Key, Transmission] | None = None
    _selectedTransmissionKey: Transmission.Key | None = None
    _startTime: DateTime | None = None
    _endTime: DateTime | None = None
    _searchText: str = ""
    _index: TransmissionsIndex | None = None

    @property
    def _selectedTransmission(self) -> Transmission | None:
        if self._selectedTransmissionKey is None:
            return None
        assert self._transmissions is not None
        return self._transmissions[self._selectedTransmissionKey]

    def _filterTransmission(self, transmission: Transmission) -> bool:
        return transmission.eventID == self._selectedEvent and transmission.isInRange(
            self._startTime, self._endTime
        )

    @var(cache=True)
    def events(self) -> list[str]:
        if self._events is None:
            return []
        return self._events

    @var(cache=True)
    def selectedEvent(self) -> str | None:
        return self._selectedEvent

    @var(cache=True)
    def transmissions(self) -> list[RXTransmission] | None:
        if self._transmissions is None:
            return None
        return [
            RXTransmission.fromTransmission(tx)
            for tx in self._transmissions.values()
            if self._filterTransmission(tx)
        ]

    @var(cache=True)
    def transmissionsCount(self) -> int:
        if self._transmissions is None:
            return 0
        return len(self._transmissions)

    @var(cache=True)
    def selectedTransmission(self) -> RXTransmission | None:
        return RXTransmission.fromTransmission(self._selectedTransmission)

    @var(cache=True)
    def selectedTransmissionAudioURL(self) -> str | None:
        # FIXME: This creates a "data:" URL containing the audio for the selected
        # recording. It works but it requires reading the audio, encoding the data
        # into a URL, and shuttling that data to the client, all of which happens
        # whether the user plays the audio or not.
        # What we should have is an endpoint for each transmission's audio.
        transmission = self._selectedTransmission
        if transmission is None:
            return None
        return dataURLFromPath(transmission.path, mimeType="audio/wav")

    @var(cache=False)
    def startTime(self) -> str:
        return htmlLocalDateTimeTextFromDateTime(self._startTime)

    @var(cache=True)
    def endTime(self) -> str:
        return htmlLocalDateTimeTextFromDateTime(self._endTime)

    @event
    async def load(self) -> None:
        try:
            store = await Global.storeFactory.store()
        except FileNotFoundError as e:
            log.error("DB file not found: {error}", error=e)
            return

        self._events = sorted(e.id for e in await store.events())
        self._transmissions = {tx.key: tx for tx in await store.transmissions()}
        self._startTime = DateTime(
            year=2000, month=1, day=1, hour=0, minute=0, tzinfo=TZInfo.PDT.value
        )
        self._endTime = DateTime.now().astimezone(TZInfo.PDT.value)

        self._index = await Global.searchIndexFactory.index(store)

    @event
    async def eventSelected(self, event: str) -> None:
        log.info("Event selected: {event!r}", event=event)
        # Note that event is the triggered Reflex event, which happens to be a
        # string that happens to also be the ID of the selected event.
        self._selectedEvent = event

    @event
    async def startTimeEdited(self, event: str) -> None:
        log.info(
            "Start time editing: {t1} -> {t2}", t1=self._startTime, t2=self.startTime
        )
        self._startTime = dateTimeFromHTMLLocalDateTimeText(event)
        log.info(
            "Start time edited: {t1} -> {t2}", t1=self._startTime, t2=self.startTime
        )

    @event
    async def endTimeEdited(self, event: str) -> None:
        log.info("End time editing: {t1} -> {t2}", t1=self._endTime, t2=self.endTime)
        self._endTime = dateTimeFromHTMLLocalDateTimeText(event)
        log.info("End time edited: {t1} -> {t2}", t1=self._endTime, t2=self.endTime)

    @event
    async def searchEdited(self, event: str) -> None:
        self._searchText = event
        log.info("Search text edited: {text!r}", text=self._searchText)

    @event
    async def rowSelected(self, event: dict[str, Any]) -> None:
        transmission = event["data"]
        self._selectedTransmissionKey = (
            transmission["eventID"],
            transmission["system"],
            transmission["channel"],
            dateTimeFromText(transmission["startTime"], RXTransmission.dateTimeFormat),
        )
