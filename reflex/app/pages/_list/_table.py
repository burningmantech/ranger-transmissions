"""
Transmissions List Table
"""

from reflex_ag_grid import ag_grid

from reflex import (
    Component,
)

from ._state import State


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
