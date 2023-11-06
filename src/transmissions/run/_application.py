from collections.abc import Iterable
from datetime import datetime as DateTime
from enum import StrEnum, auto
from typing import Any, ClassVar, cast

from arrow import get as makeArrow
from rich.markup import escape
from rich.text import Text
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


def optionalEscape(text: str | None) -> str | None:
    if text is None:
        return None
    else:
        return escape(text)


def dateTimeAsText(datetime: DateTime) -> str:
    return str(makeArrow(datetime))


def dateTimeFromText(text: str) -> DateTime:
    return makeArrow(text).datetime


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
            color: $text;
            background: $primary-darken-2;
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
            color: $text-muted;
            background: $primary-darken-3;
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

    class QueryUpdated(Message):
        """
        Search field updated message.
        """

        def __init__(self, control: Widget, query: str):
            self._control = control
            self.query = query
            super().__init__()

        @property
        def control(self) -> Widget:
            return self._control

    def compose(self) -> ComposeResult:
        yield Input(
            id="SearchField",
            placeholder=" \N{right-pointing magnifying glass} Search...",
        )

    @on(Input.Submitted)
    def handle_update(self, message: Input.Changed) -> None:
        query = message.value
        self.post_message(self.QueryUpdated(self, query))


TransmissionTableRowItems = tuple[
    str,  # event
    str,  # station
    str,  # system
    str,  # channel
    str,  # startTime -> text
    Text | None,  # duration -> rich text
    str,  # path
    str | None,  # sha256
    str | None,  # transcription
]
TransmissionTableRowData = tuple[TransmissionTableRowItems, str]
TransmissionTableData = tuple[TransmissionTableRowData, ...]


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
    displayColumns = reactive(
        frozenset(
            (
                Column.event,
                Column.station,
                # Column.system,
                Column.channel,
                Column.startTime,
                Column.duration,
                # Column.path,
                # Column.sha256,
                Column.transcription,
            )
        )
    )
    dateTimeDisplayFormat = reactive("ddd YY/MM/DD HH:mm:ss")
    timeZone = reactive("US/Pacific")
    searchQuery = reactive("")

    def __init__(self, id: str) -> None:
        self._tableData: TransmissionTableData = ()
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield DataTable(
            cursor_type="row",
            zebra_stripes=True,
        )

    def on_mount(self) -> None:
        headerNames = {
            self.Column.event: "Event",
            self.Column.station: "Station",
            self.Column.system: "System",
            self.Column.channel: "Channel",
            self.Column.startTime: "Start",
            self.Column.duration: "Duration",
            self.Column.path: "Path",
            self.Column.sha256: "SHA256",
            self.Column.transcription: "Transcription",
        }

        table = self.query_one(DataTable)
        for column in self.Column:
            if column in self.displayColumns:
                table.add_column(headerNames[column], key=column)

    def dateTimeAsDisplayText(self, dateTime: DateTime) -> str:
        arrow = makeArrow(dateTime).to(self.timeZone)
        return arrow.format(self.dateTimeDisplayFormat)

    def dateTimeTextAsDisplayText(self, text: str) -> str:
        dateTime = dateTimeFromText(text)
        return self.dateTimeAsDisplayText(dateTime)

    def dateTimeFromDisplayText(self, displayText: str) -> DateTime:
        arrow = makeArrow(displayText, self.dateTimeDisplayFormat)
        return arrow.datetime

    def filterTable(self, row: TransmissionTableRowItems, key: str) -> bool:
        query = self.searchQuery
        if not query:
            return True

        transcription = row[8]

        if not transcription:
            return False

        for term in query.split():
            if term:
                term = term.lower()
                if transcription.lower().find(term) != -1:
                    continue
            break
        else:
            return True

        return False

    def updateTable(self) -> None:
        self.log("Updating table")
        columns = []

        if self.Column.event in self.displayColumns:
            columns.append(0)
        if self.Column.station in self.displayColumns:
            columns.append(1)
        if self.Column.system in self.displayColumns:
            columns.append(2)
        if self.Column.channel in self.displayColumns:
            columns.append(3)
        if self.Column.startTime in self.displayColumns:
            columns.append(4)
        if self.Column.duration in self.displayColumns:
            columns.append(5)
        if self.Column.path in self.displayColumns:
            columns.append(6)
        if self.Column.sha256 in self.displayColumns:
            columns.append(7)
        if self.Column.transcription in self.displayColumns:
            columns.append(8)

        table = self.query_one(DataTable)
        table.clear()
        for row, key in self._tableData:
            if self.filterTable(row, key):
                table.add_row(*[row[column] for column in columns], key=key)

        def sortKey(startTime: str) -> Any:
            return self.dateTimeFromDisplayText(startTime)

        table.sort(self.Column.startTime, key=sortKey)

    def updateTransmissions(self) -> None:
        self.log(f"Updating {len(self.transmissions)} transmissions")
        tableData: list[TransmissionTableRowData] = []

        for transmission in self.transmissions:
            key = transmission[0]
            eventID = transmission[1]
            station = transmission[2]
            system = transmission[3]
            channel = transmission[4]
            startTime = transmission[5]
            duration = transmission[6]
            path = transmission[7]
            sha256 = transmission[8]
            transcription = transmission[9]

            if duration is None:
                durationItem = None
            else:
                durationItem = Text(escape(f"{duration}s"), justify="right")

            items: TransmissionTableRowItems = (
                escape(eventID),
                escape(station),
                escape(system),
                escape(channel),
                escape(self.dateTimeTextAsDisplayText(startTime)),
                durationItem,
                escape(path),
                optionalEscape(sha256),
                optionalEscape(transcription),
            )

            rowData: TransmissionTableRowData = (items, key)
            tableData.append(rowData)

        self._tableData = tuple(tableData)
        self.updateTable()

    def watch_transmissions(
        self, transmissions: tuple[TransmissionTuple, ...]
    ) -> None:
        self.log(f"Received {len(self.transmissions)} transmissions")
        try:
            self.updateTransmissions()
        except Exception as e:
            self.log(f"Unable to update transmissions: {e}")

    def watch_searchQuery(self, searchQuery: str) -> None:
        self.log(f"Received search query: {searchQuery}")
        try:
            self.updateTable()
        except Exception as e:
            self.log(f"Unable to update table: {e}")

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
            border: double $accent;
            background: $boost;
        }
        """

    BORDER_TITLE = "Transmission Details"

    transmission: reactive[TransmissionTuple | None] = reactive(None)
    showFileInfo = reactive(False)
    dateTimeDisplayFormat = reactive("[on] ddd YY/MM/DD [at] HH:mm:ss")
    timeZone = reactive("US/Pacific")

    def dateTimeAsDisplayText(self, dateTime: DateTime) -> str:
        arrow = makeArrow(dateTime).to(self.timeZone)
        return arrow.format(self.dateTimeDisplayFormat)

    def dateTimeTextAsDisplayText(self, text: str) -> str:
        dateTime = dateTimeFromText(text)
        return self.dateTimeAsDisplayText(dateTime)

    def updateDetails(self) -> None:
        if self.transmission is None:
            return

        # key: str = self.transmission[0]
        eventID: str = escape(self.transmission[1])
        station: str = escape(self.transmission[2])
        system: str = escape(self.transmission[3])
        channel: str = escape(self.transmission[4])
        startTime: str = escape(
            self.dateTimeTextAsDisplayText(self.transmission[5])
        )
        duration: float | None = self.transmission[6]
        path: str = escape(self.transmission[7])
        sha256: str | None = optionalEscape(self.transmission[8])
        transcription: str | None = optionalEscape(self.transmission[9])

        details: list[str] = []

        details.append(
            f"([bold yellow]{eventID}[/bold yellow])"
            f" Station [bold yellow]{station}[/bold yellow]"
            f" on {system} [bold yellow]{channel}[/bold yellow]"
            f" {startTime} ({duration}s)"
        )

        if self.showFileInfo:
            if sha256 is None:
                details.append(path)
            else:
                details.append(f"SHA {sha256}: {path}")

        details.append("")

        if transcription is None:
            details.append("[i](transcription not available)[/i]")
        else:
            details.append(transcription.strip())

        self.update("\n".join(details))

    def watch_transmission(self, transmission: str) -> None:
        try:
            self.updateDetails()
        except Exception as e:
            self.log(f"Unable to update transmission details: {e}")


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
        yield BodyContainer(id="Body")

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


class TransmissionsApp(App):
    """
    Transmissions application.
    """

    TITLE = "Transmissions"
    SUB_TITLE = ""

    BINDINGS = [
        ("d", "dark", "Toggle dark mode"),
        ("q", "quit", "Quit application"),
    ]

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

    async def action_dark(self) -> None:
        self.dark = not self.dark
