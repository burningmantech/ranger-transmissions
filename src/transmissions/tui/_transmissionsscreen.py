from typing import ClassVar, cast

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen

from transmissions.model import Transmission
from transmissions.search import TransmissionsIndex

from ._body import Body
from ._footer import Footer
from ._header import Header
from ._searchfield import SearchField
from ._transmissiondetails import TransmissionDetails
from ._transmissionlist import TransmissionList
from ._util import TransmissionTuple, dateTimeAsText


__all__ = ()


def transmissionTableKey(key: Transmission.Key) -> str:
    return ":".join(str(i) for i in key)


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

    def __init__(self, transmissions: tuple[Transmission, ...]) -> None:
        self.transmissionsByKey = {
            transmissionTableKey(transmission.key): transmission
            for transmission in transmissions
        }

        super().__init__()

    async def on_mount(self) -> None:
        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        transmissionList.transmissions = tuple(
            transmissionAsTuple(key, transmission)
            for key, transmission in self.transmissionsByKey.items()
        )

        try:
            transmissionsIndex = TransmissionsIndex()
            await transmissionsIndex.connect()
            await transmissionsIndex.add(self.transmissionsByKey.values())
            self._transcriptionsIndex = transmissionsIndex
        except Exception as e:
            self.log(f"Unable to index transmissions: {e}")

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
        transmission = self.transmissionsByKey[message.key]
        self.log(f"Transmission selected: {transmission}")

        # Pass down to details view
        transmissionDetails = cast(
            TransmissionDetails, self.query_one("TransmissionDetails")
        )
        transmissionDetails.transmission = transmissionAsTuple(
            message.key, transmission
        )

    @on(SearchField.QueryUpdated)
    async def handleSearchQueryUpdated(
        self, message: SearchField.QueryUpdated
    ) -> None:
        self.log(f"Search query: {message.query}")

        searchQuery = message.query.strip()

        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        transmissionList.searchQuery = searchQuery

        if searchQuery:
            try:
                keys = frozenset(
                    {
                        transmissionTableKey(result)
                        async for result in self._transcriptionsIndex.search(
                            message.query
                        )
                    }
                )
                self.log(f"{keys}")
                transmissionList.displayKeys = keys
            except Exception as e:
                self.log(f"Unable to perform search: {e}")
        else:
            transmissionList.displayKeys = None
