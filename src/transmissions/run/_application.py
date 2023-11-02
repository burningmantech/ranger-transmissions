from typing import ClassVar, cast

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DataTable, Input, Static

from transmissions.model import Transmission


__all__ = ()


class Header(Static):
    """
    App header.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        Header {
            height: 3;
            dock: top;
            content-align: center middle;
        }
        """


class Footer(Static):
    """
    App footer.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        Footer {
            height: 1;
            dock: bottom;
            content-align: center middle;
        }
        """


class BodyContainer(Static):
    """
    Container for the application body.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        BodyContainer {
            width: 1fr;
            height: 1fr;
        }
        """

    def compose(self) -> ComposeResult:
        yield SearchField()
        yield TransmissionList(id="TransmissionList")
        yield TransmissionDetails(id="TransmissionDetails")


class SearchField(Static):
    """
    Search field.
    """

    def compose(self) -> ComposeResult:
        yield Input(
            id="SearchField",
            placeholder=" \N{right-pointing magnifying glass} Search...",
        )


class TransmissionList(VerticalScroll):
    """
    List of transmissions.
    """

    transmissions = reactive(0)

    def compose(self) -> ComposeResult:
        yield DataTable()

    def watch_transmissions(
        self, transmissions: frozenset[Transmission]
    ) -> None:
        self.updateTransmissions()

    @staticmethod
    def keyForTransmission(transmission: Transmission) -> str:
        return ":".join(
            (
                transmission.eventID,
                transmission.system,
                transmission.channel,
                str(transmission.startTime),
            )
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Event")
        table.add_column("Station")
        table.add_column("System")
        table.add_column("Channel")
        table.add_column("Start")
        table.add_column("Duration")
        table.add_column("Text")
        table.add_column("Path")
        table.add_column("SHA256")

    def updateTransmissions(self) -> None:
        self.log(f"Updating transmissions ({self.transmissions})")
        # table = self.query_one(DataTable)
        # table.clear()
        # for transmission in self.transmissions:
        #     table.add_row(
        #         transmission.eventID,
        #         transmission.station,
        #         transmission.system,
        #         transmission.channel,
        #         "start",
        #         "duration",
        #         transmission.sha256,
        #         transmission.transcription,
        #     )


class TransmissionDetails(Static):
    """
    Transmission detail view.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        TransmissionDetails {
            height: 10;
            dock: bottom;
        }
        """


class TransmissionsScreen(Screen):
    """
    Transmissions screen.
    """

    def __init__(self, transmissions: frozenset[Transmission]) -> None:
        self.transmissions = transmissions
        super().__init__()

    async def on_mount(self) -> None:
        self.log("Looking for transmissions list...")
        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        self.log(f"Found transmissions list {transmissionList}")
        transmissionList.transmissions = len(self.transmissions)

    def compose(self) -> ComposeResult:
        yield Header("Radio Transmissions", id="Header")
        yield Footer(
            "Copyright © Burning Man"
            " - Audio and displayed content is confidential and proprietary",
            id="Footer",
        )
        yield BodyContainer(id="Body")


class TransmissionsApp(App):
    """
    Transmissions application.
    """

    TITLE = "Transmissions"
    SUB_TITLE = ""

    BINDINGS = [("q", "quit", "Quit application")]

    def __init__(self, transmissions: frozenset[Transmission]) -> None:
        self.transmissions = transmissions
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen(TransmissionsScreen(self.transmissions))

    async def action_quit(self) -> None:
        self.exit()
