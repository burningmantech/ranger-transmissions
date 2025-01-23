"""
Transmissions Table
"""

from reflex_ag_grid import ag_grid
from twisted.logger import Logger

import app as Global
from app.model import RXTransmission
from reflex import Component, State, container, page, vstack


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
            ]


column_defs = [
    ag_grid.column_def(
        field="eventID", header_name="Event", filter=ag_grid.filters.text
    ),
    ag_grid.column_def(
        field="startTime", header_name="Start Time", filter=ag_grid.filters.date
    ),
    ag_grid.column_def(
        field="duration", header_name="Duration", filter=ag_grid.filters.number
    ),
    ag_grid.column_def(
        field="channel", header_name="Channel", filter=ag_grid.filters.text
    ),
    ag_grid.column_def(
        field="station", header_name="Station", filter=ag_grid.filters.text
    ),
    ag_grid.column_def(
        field="transcription", header_name="Transcript", filter=ag_grid.filters.text
    ),
]


def transmissionsTable() -> Component:
    return ag_grid(
        id="transmissions_table",
        row_data=State.transmissions,
        column_defs=column_defs,
        pagination=True,
        pagination_page_size=50,
        pagination_page_size_selector=[25, 50, 100],
        width="100%",
        height="95vh",
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
