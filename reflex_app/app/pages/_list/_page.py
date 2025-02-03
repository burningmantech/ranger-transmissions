"""
Transmissions List page
"""

from reflex import (
    Component,
    heading,
    page,
    text,
    vstack,
)

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
        transmissionsTable(),
        text(State.transmissionsCount, " transmissions"),
        selectedTransmissionInfo(),
        spacing="4",
        margin="1vh",
        height="100vh",
    )
