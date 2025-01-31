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
    State,
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
from transmissions.model import Transmission


log = Logger()


def dataURLFromPath(path: Path, *, mimeType: str) -> str:
    with path.open("rb") as f:
        data = f.read()
    b64Text = b64encode(data).decode("utf-8")
    return f"data:{mimeType};base64,{b64Text}"


class TransmissionsTableState(State):
    """
    Transmissions table state.
    """

    _transmissions: dict[Transmission.Key, Transmission] = None
    _selectedTransmissionKey: Transmission.Key | None = None

    @var(cache=True)
    def transmissions(self) -> list[RXTransmission] | None:
        if self._transmissions is None:
            return None
        return [
            RXTransmission.fromTransmission(t) for t in self._transmissions.values()
        ]

    @var(cache=True)
    def selectedTransmission(self) -> RXTransmission | None:
        if self._selectedTransmissionKey is None:
            return None

        return RXTransmission.fromTransmission(
            self._transmissions[self._selectedTransmissionKey]
        )

    @var(cache=True)
    def selectedTransmissionAudioURL(self) -> str | None:
        if self._selectedTransmissionKey is None:
            return None

        # FIXME: This creates a "data:" URL containing the audio for the selected
        # recording. It works but it requires reading the audio, encoding the data
        # into a URL, and shuttling that data to the client, all of which happens
        # whether the user plays the audio or not.
        # What we should have is an endpoint for each transmission's audio.
        transmission = self._transmissions[self._selectedTransmissionKey]
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
            DateTime.fromisoformat(transmission["startTime"]),
        )


column_defs = [
    ag_grid.column_def(
        field="eventID",
        header_name="Event",
        filter=ag_grid.filters.text,
        initialWidth=70,
    ),
    ag_grid.column_def(
        field="startTime",
        header_name="Start Time",
        filter=ag_grid.filters.text,
        initialWidth=185,
    ),
    ag_grid.column_def(
        field="duration",
        header_name="Duration",
        filter=ag_grid.filters.number,
        initialWidth=80,
    ),
    ag_grid.column_def(
        field="channel",
        header_name="Channel",
        filter=ag_grid.filters.text,
        initialWidth=150,
    ),
    ag_grid.column_def(
        field="station",
        header_name="Station",
        filter=ag_grid.filters.text,
        initialWidth=150,
    ),
    ag_grid.column_def(
        field="transcription",
        header_name="Transcript",
        filter=ag_grid.filters.text,
        initialWidth=5000,
    ),
]


def transmissionsTable() -> Component:
    """
    Transmissions table
    """
    return ag_grid(
        id="transmissions_table",
        row_data=TransmissionsTableState.transmissions,
        column_defs=column_defs,
        on_mount=TransmissionsTableState.load,
        on_row_clicked=TransmissionsTableState.rowSelected,
        theme="alpine",
        width="100%",
        height="50vh",
    )


def selectedTransmissionInfo() -> Component:
    """
    Information about the selected transmission.
    """
    transmission = TransmissionsTableState.selectedTransmission

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
                text("SHA256: ", code(transmission.sha256), size="1"),
                divider(),
                text("Transcript:"),
                blockquote(transmission.transcription),
                divider(),
                audio(
                    url=TransmissionsTableState.selectedTransmissionAudioURL,
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
        selectedTransmissionInfo(),
        spacing="4",
        margin="1vh",
        height="100vh",
    )
