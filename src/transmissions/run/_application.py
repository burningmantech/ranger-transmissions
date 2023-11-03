from collections.abc import Iterable
from datetime import datetime as DateTime
from enum import StrEnum, auto
from typing import Any, ClassVar, cast

from arrow import get as makeArrow
from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from transmissions.model import Transmission


__all__ = ()


TransmissionTuple = tuple[
    str, str, str, str, str, str, float | None, str, str | None, str | None
]


def transmissionKey(transmission: Transmission) -> str:
    return ":".join(
        (
            transmission.eventID,
            transmission.system,
            transmission.channel,
            str(transmission.startTime),
        )
    )


_dateTimeDisplayFormat = "ddd MM/DD HH:mm:ss"


def dateTimeAsText(datetime: DateTime) -> str:
    arrow = makeArrow(datetime).to("US/Pacific")
    return arrow.format(_dateTimeDisplayFormat)


def dateTimeFromText(text: str) -> DateTime:
    arrow = makeArrow(text, _dateTimeDisplayFormat)
    return arrow.datetime


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


class TransmissionList(Static):
    """
    List of transmissions.
    """

    class Column(StrEnum):
        """
        Column Keys
        """

        event = auto()
        station = auto()
        system = auto()
        channel = auto()
        startTime = auto()
        duration = auto()
        path = auto()
        sha256 = auto()
        transcription = auto()

    class TransmissionSelected(Message):
        """
        Transmission selected message.
        """

        def __init__(self, control: Widget, key: str):
            self._control = control
            self.key = key
            super().__init__()

        @property
        def control(self) -> Widget:
            return self._control

    transmissions: reactive[tuple[TransmissionTuple, ...]] = reactive(())

    def compose(self) -> ComposeResult:
        yield DataTable(
            cursor_type="row",
            zebra_stripes=True,
        )

    def watch_transmissions(self, transmissions: tuple[int]) -> None:
        self.updateTransmissions()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Event", key=self.Column.event)
        table.add_column("Station", key=self.Column.station)
        table.add_column("System", key=self.Column.system)
        table.add_column("Channel", key=self.Column.channel)
        table.add_column("Start", key=self.Column.startTime)
        # table.add_column("Duration", key=self.Column.duration)
        # table.add_column("Path", key=self.Column.path)
        # table.add_column("SHA256", key=self.Column.sha256)
        table.add_column("Transcription", key=self.Column.transcription)

    def updateTransmissions(self) -> None:
        self.log(f"Displaying {len(self.transmissions)} transmissions")
        table = self.query_one(DataTable)
        table.clear()
        for transmission in self.transmissions:
            table.add_row(
                transmission[1],  # eventID
                transmission[2],  # station
                transmission[3],  # system
                transmission[4],  # channel
                transmission[5],  # startTime
                # transmission[6],  # duration
                # transmission[7],  # path
                # transmission[8],  # sha256
                transmission[9],  # transcription
                key=transmission[0],
            )

        def sortKey(startTime: str) -> Any:
            return dateTimeFromText(startTime)

        table.sort(self.Column.startTime, key=sortKey)

    @on(DataTable.RowSelected)
    def handle_row_selected(self, message: DataTable.RowSelected) -> None:
        key = message.row_key.value
        assert key is not None
        self.post_message(self.TransmissionSelected(self, key))


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

    def __init__(self, transmissions: dict[str, Transmission]) -> None:
        self.transmissions = transmissions
        super().__init__()

    async def on_mount(self) -> None:
        transmissionList = cast(
            TransmissionList, self.query_one("TransmissionList")
        )
        transmissions = tuple(
            transmissionAsTuple(key, transmission)
            for key, transmission in self.transmissions.items()
        )
        transmissionList.transmissions = transmissions

    def compose(self) -> ComposeResult:
        yield Header("Radio Transmissions", id="Header")
        yield Footer(
            "Copyright © Burning Man"
            " - Audio and displayed content is confidential and proprietary",
            id="Footer",
        )
        yield BodyContainer(id="Body")

    @on(TransmissionList.TransmissionSelected)
    def handle_transmission_selected(
        self, message: TransmissionList.TransmissionSelected
    ) -> None:
        transmission = self.transmissions[message.key]
        self.log(f"Transmission selected: {transmission}")


class TransmissionsApp(App):
    """
    Transmissions application.
    """

    TITLE = "Transmissions"
    SUB_TITLE = ""

    BINDINGS = [("q", "quit", "Quit application")]

    def __init__(self, transmissions: Iterable[Transmission]) -> None:
        self.transmissions = {
            transmissionKey(transmission): transmission
            for transmission in transmissions
        }
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen(TransmissionsScreen(self.transmissions))

    async def action_quit(self) -> None:
        self.exit()
