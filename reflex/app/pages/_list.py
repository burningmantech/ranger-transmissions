"""
Transmissions Table
"""

from base64 import b64encode
from datetime import datetime as DateTime
from pathlib import Path

from reflex_ag_grid import ag_grid
from twisted.logger import Logger

import app as Global
from app.model import RXTransmission
from reflex import (
    Component,
    audio,
    blockquote,
    card,
    code,
    cond,
    divider,
    event,
    heading,
    page,
    text,
    var,
    vstack,
)
from reflex import State as BaseState
from transmissions.model import Transmission, TZInfo


log = Logger()


def dataURLFromPath(path: Path, *, mimeType: str) -> str:
    with path.open("rb") as f:
        data = f.read()
    b64Text = b64encode(data).decode("utf-8")
    return f"data:{mimeType};base64,{b64Text}"


class State(BaseState):
    """
    Transmissions table state.
    """

    _transmissions: dict[Transmission.Key, Transmission] = None
    _selectedTransmissionKey: Transmission.Key | None = None

    @property
    def _selectedTransmission(self) -> Transmission | None:
        if self._selectedTransmissionKey is None:
            return None
        return self._transmissions[self._selectedTransmissionKey]

    @var(cache=True)
    def transmissions(self) -> list[RXTransmission] | None:
        if self._transmissions is None:
            return None
        return [
            RXTransmission.fromTransmission(t) for t in self._transmissions.values()
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

    @event
    async def load(self) -> None:
        try:
            store = await Global.storeFactory.store()
        except FileNotFoundError as e:
            log.error("DB file not found: {error}", error=e)
        else:
            self._transmissions = {t.key: t for t in await store.transmissions()}

        log.info("{count} transmissions loaded", count=len(self.transmissions))

    @event
    async def rowSelected(self, event: dict) -> None:
        transmission = event["data"]
        self._selectedTransmissionKey = (
            transmission["eventID"],
            transmission["system"],
            transmission["channel"],
            DateTime.strptime(
                transmission["startTime"], RXTransmission.dateTimeFormat
            ).replace(tzinfo=TZInfo.PDT.value),
        )


column_defs = [
    ag_grid.column_def(
        field="eventID",
        header_name="Event",
        initialWidth=70,
    ),
    ag_grid.column_def(
        field="startTime",
        header_name="Start Time",
        initialWidth=180,
    ),
    ag_grid.column_def(
        field="duration",
        header_name="Duration",
        initialWidth=80,
    ),
    ag_grid.column_def(
        field="channel",
        header_name="Channel",
        initialWidth=150,
    ),
    ag_grid.column_def(
        field="station",
        header_name="Station",
        initialWidth=150,
    ),
    ag_grid.column_def(
        field="transcription",
        header_name="Transcript",
        initialWidth=800,
    ),
]


def transmissionsTable() -> Component:
    """
    Transmissions table
    """
    return ag_grid(
        id="transmissions_table",
        row_data=State.transmissions,
        column_defs=column_defs,
        on_mount=State.load,
        on_row_clicked=State.rowSelected,
        theme="alpine",
        width="100%",
        height="50vh",
    )


def selectedTransmissionInfo() -> Component:
    """
    Information about the selected transmission.
    """
    transmission = State.selectedTransmission

    return cond(
        transmission,
        card(
            vstack(
                heading("Selected Transmission", as_="h2"),
                divider(),
                text(
                    "Station ",
                    code(transmission.station),
                    " on channel ",
                    code(transmission.channel),
                    " at ",
                    text.strong(transmission.startTime),
                ),
                divider(),
                text("Transcript:"),
                blockquote(transmission.transcription),
                divider(),
                audio(
                    url=State.selectedTransmissionAudioURL,
                    width="100%",
                    height="32px",
                ),
                width="100%",
            ),
            width="100%",
        ),
        card(
            vstack(
                text("No transmission selected"),
                width="100%",
            ),
            width="100%",
        ),
    )


@page(route="/", title="Transmissions List")
def transmissionsListPage() -> Component:
    """
    Transmissions table page
    """
    return vstack(
        heading("Transmissions List"),
        transmissionsTable(),
        text(State.transmissionsCount, " transmissions"),
        selectedTransmissionInfo(),
        spacing="4",
        margin="1vh",
        height="100vh",
    )
