from typing import ClassVar, cast

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen

from transmissions.model import Transmission

from ._body import Body
from ._footer import Footer
from ._header import Header
from ._searchfield import SearchField
from ._transmissiondetails import TransmissionDetails
from ._transmissionlist import TransmissionList
from ._util import TransmissionTuple, dateTimeAsText


__all__ = ()


def transmissionAsTuple(
    key: str, transmission: Transmission
) -> TransmissionTuple:
    if transmission.duration is None:
        duration = None
    else:
        duration = transmission.duration.total_seconds()

    return (
        key,
        transmission.eventID,
        transmission.station,
        transmission.system,
        transmission.channel,
        dateTimeAsText(transmission.startTime),
        duration,
        str(transmission.path),
        transmission.sha256,
        transmission.transcription,
    )


class TransmissionsScreen(Screen):
    """
    Transmissions screen.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        TransmissionsScreen {
            background: $background-darken-3;
        }
        """

    def __init__(self, transmissions: dict[str, Transmission]) -> None:
        self.transmissions = transmissions
        super().__init__()

    async def on_mount(self) -> None:
        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        transmissionList.transmissions = tuple(
            transmissionAsTuple(key, transmission)
            for key, transmission in self.transmissions.items()
        )

    def compose(self) -> ComposeResult:
        yield Header("Radio Transmissions", id="Header")
        yield Footer(
            "Copyright © Burning Man"
            " - Audio and displayed content is confidential and proprietary",
            id="Footer",
        )
        yield Body(id="Body")

    @on(TransmissionList.TransmissionSelected)
    def handleTransmissionSelected(
        self, message: TransmissionList.TransmissionSelected
    ) -> None:
        transmission = self.transmissions[message.key]
        self.log(f"Transmission selected: {transmission}")

        # Pass down to details view
        transmissionDetails = cast(
            TransmissionDetails, self.query_one("TransmissionDetails")
        )
        transmissionDetails.transmission = transmissionAsTuple(
            message.key, transmission
        )

    @on(SearchField.QueryUpdated)
    def handleSearchQueryUpdated(
        self, message: SearchField.QueryUpdated
    ) -> None:
        self.log(f"Search query: {message.query}")
        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        transmissionList.searchQuery = message.query
