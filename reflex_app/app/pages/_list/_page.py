"""
Transmissions List page
"""

from reflex import Component, cond, heading, page, text, vstack

from ._filters import transmissionsFilters
from ._info import selectedTransmissionInfo
from ._state import State
from ._table import transmissionsTable


__all__ = [
    "transmissionsListPage",
]


@page(route="/", title="Transmissions List")
def transmissionsListPage() -> Component:
    """
    Transmissions table page
    """
    return vstack(
        heading("Transmissions List"),
        transmissionsFilters(),
        transmissionsTable(),
        cond(
            State.transmissions,
            text(
                "Displaying ",
                State.transmissions.length(),
                " of ",
                State.transmissionsCount,
                " transmissions",
            ),
        ),
        selectedTransmissionInfo(),
        spacing="4",
        margin="1vh",
        height="100vh",
    )
