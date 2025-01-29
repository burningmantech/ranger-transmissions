"""
Transmissions Table
"""

from base64 import b64encode
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
    fragment,
    heading,
    page,
    text,
    vstack,
)


log = Logger()


def dataURLFromPath(path: Path, mimeType: str) -> str:
    with path.open("rb") as f:
        data = f.read()
    b64Text = b64encode(data).decode("utf-8")
    return f"data:{mimeType};base64,{b64Text}"


class TransmissionsTableState(State):
    """
    Transmissions table state.
    """

    transmissions: list[RXTransmission]

    selectedTransmission: dict
    audioURL: str = ""

    @event
    async def load(self) -> None:
        self.selectedTransmission = {}

        try:
            store = await Global.storeFactory.store()
        except FileNotFoundError as e:
            log.error("DB file not found: {error}", error=e)
        else:
            self.transmissions = [
                RXTransmission.fromTransmission(t) for t in await store.transmissions()
            ]

        log.info("{count} transmissions loaded", count=len(self.transmissions))

    @event
    async def rowSelected(self, event: dict) -> None:
        tx = event["data"]
        self.selectedTransmission = tx

        # FIXME: This creates a "data:" URL containing the audio for the selected
        # recording. It works but it requires reading the audio, encoding the data
        # into a URL, and shuttling that data to the client, all of which happens
        # whether the user plays the audio or not.
        # What we should have is an endpoint for each transmission's audio.
        self.audioURL = dataURLFromPath(Path(tx["path"]), "audio/wav")


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
        # pagination=True,
        # pagination_page_size=50,
        # pagination_page_size_selector=[10, 25, 50, 100],
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
    tx = TransmissionsTableState.selectedTransmission

    return cond(
        tx,
        card(
            vstack(
                heading("Selected Transmission", as_="h2"),
                divider(),
                text(
                    "Station ",
                    code(tx.station),
                    " on channel ",
                    code(tx.channel),
                    " at ",
                    text.strong(tx.startTime),
                ),
                text("File: ", code(tx.path), size="1"),
                text("SHA256: ", code(tx.sha256), size="1"),
                divider(),
                text("Transcript:"),
                blockquote(tx.transcription),
                divider(),
                audio(
                    url=TransmissionsTableState.audioURL,
                    width="100%",
                    height="32px",
                ),
                width="100%",
            ),
            width="100%",
        ),
        fragment(),
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
