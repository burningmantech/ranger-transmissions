from collections.abc import Sequence
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


def transmissionAsTuple(key: str, transmission: Transmission) -> TransmissionTuple:
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

    BINDINGS: ClassVar = [("space", "play", "Play transmission")]

    DEFAULT_CSS: ClassVar[str] = """
        TransmissionsScreen {
            background: $background-darken-3;
        }
        """

    def __init__(
        self,
        transmissions: Sequence[Transmission],
        searchIndex: TransmissionsIndex,
    ) -> None:
        self.transmissionsByKey = {
            transmissionTableKey(transmission.key): transmission
            for transmission in transmissions
        }
        self.selectedTransmission: Transmission | None = None
        self.searchIndex = searchIndex

        super().__init__()

    async def on_mount(self) -> None:
        transmissionList = cast(TransmissionList, self.query_one("TransmissionList"))
        transmissionList.transmissions = tuple(
            transmissionAsTuple(key, transmission)
            for key, transmission in self.transmissionsByKey.items()
        )
        footer = cast(Footer, self.query_one("Footer"))
        footer.totalTransmissions = footer.displayedTransmissions = len(
            self.transmissionsByKey
        )

    def compose(self) -> ComposeResult:
        yield Header("Radio Transmissions", id="Header")
        yield Footer(id="Footer")
        yield Body(id="Body")

    @on(TransmissionList.TransmissionSelected)
    def handleTransmissionSelected(
        self, message: TransmissionList.TransmissionSelected
    ) -> None:
        self.selectedTransmission = self.transmissionsByKey[message.key]
        self.log(f"Transmission selected: {self.selectedTransmission}")

        # Pass down to details view
        transmissionDetails = cast(
            TransmissionDetails, self.query_one("TransmissionDetails")
        )
        transmissionDetails.transmission = transmissionAsTuple(
            message.key, self.selectedTransmission
        )

    @on(SearchField.QueryUpdated)
    async def handleSearchQueryUpdated(self, message: SearchField.QueryUpdated) -> None:
        searchQuery = message.query
        transmissionList = cast(TransmissionList, self.query_one("TransmissionList"))
        footer = cast(Footer, self.query_one("Footer"))

        if searchQuery:
            self.log(f"Search query: {searchQuery}")
            try:
                keys = frozenset(
                    {
                        transmissionTableKey(result)
                        async for result in self.searchIndex.search(searchQuery)
                    }
                )
                transmissionList.displayKeys = keys
                footer.displayedTransmissions = len(keys)
            except Exception as e:  # noqa: BLE001
                self.log(f"Unable to perform search: {e}")
        else:
            self.log("No search query")
            transmissionList.displayKeys = None
            footer.displayedTransmissions = len(self.transmissionsByKey)

    async def action_play(self) -> None:
        self.log(f"Play requested: {self.selectedTransmission}")

        if self.selectedTransmission is None:
            self.log("No transmission selected")
            return

        try:
            path = self.selectedTransmission.path
            if not path.is_file():
                self.log(f"No such audio file: {path}")
                return

            self.log("Playback not implemented...")
        except Exception as e:  # noqa: BLE001
            self.log(f"Play failed: {e}")
