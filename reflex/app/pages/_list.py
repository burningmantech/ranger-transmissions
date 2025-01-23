"""
Transmissions Table
"""

from twisted.logger import Logger

import app as Global
from app.model import RXTransmission
from reflex import Component, State, container, foreach, page, table, vstack


log = Logger()


class State(State):
    """
    Page state.
    """

    transmissions: list[RXTransmission]

    async def load(self) -> None:
        try:
            store = await Global.storeFactory.store()
        except FileNotFoundError as e:
            log.error("DB file not found: {error}", error=e)
        else:
            self.transmissions = [
                RXTransmission.fromTransmission(t) for t in await store.transmissions()
            ][:500]  # FIXME: Dies if data set is too big


headerNames = (
    "Event",
    "Time",
    "Duration",
    "System",
    "Channel",
    "Station",
    "Text",
)


def rowForTransmission(transmission: RXTransmission) -> Component:
    return table.row(
        table.cell(transmission.eventID),
        table.cell(transmission.startTime),
        table.cell(transmission.duration),
        table.cell(transmission.system),
        table.cell(transmission.channel),
        table.cell(transmission.station),
        table.cell(transmission.transcription),
    )


def transmissionsTable() -> Component:
    return table.root(
        table.header(
            table.row(
                foreach(headerNames, table.column_header_cell),
            ),
        ),
        table.body(
            foreach(State.transmissions, rowForTransmission),
        ),
        width="100%",
    )


@page(route="/", title="Transmissions List", on_load=State.load)
def transmissionsListPage() -> Component:
    """
    Transmissions Table page.
    """
    return container(
        vstack(
            transmissionsTable(),
            align="center",
            width="100%",
        ),
    )
