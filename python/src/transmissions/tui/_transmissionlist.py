from collections.abc import Sequence
from datetime import datetime as DateTime
from enum import StrEnum, auto

from arrow import get as makeArrow
from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static

from ._util import TransmissionTuple, dateTimeFromText


__all__ = ()


TransmissionTableRowCells = tuple[
    str,  # event
    str,  # station
    str,  # system
    str,  # channel
    str,  # startTime -> text
    str | Text,  # duration -> rich text
    str,  # path
    str | Text,  # sha256
    str,  # transcription
]
TransmissionTableRowData = tuple[TransmissionTableRowCells, str]
TransmissionTableData = Sequence[TransmissionTableRowData]


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

        def __init__(self, control: Widget, key: str) -> None:
            self._control = control
            self.key = key
            super().__init__()

        @property
        def control(self) -> Widget:
            return self._control

    transmissions: reactive[Sequence[TransmissionTuple]] = reactive(())
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
    displayKeys: reactive[frozenset[str] | None] = reactive(None)

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
            if self.displayKeys is None or key in self.displayKeys:
                table.add_row(*[row[column] for column in columns], key=key)

        # def sortKey(startTime: str) -> Any:
        #     return self.dateTimeFromDisplayText(startTime)

        # table.sort(self.Column.startTime, key=sortKey)

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
                durationCell = Text("-", justify="center")
            else:
                durationCell = Text(escape(f"{duration}s"), justify="right")

            if sha256 is None:
                sha256Cell: str | Text = Text("-", justify="center")
            else:
                sha256Cell = escape(sha256)

            if transcription is None:
                transcription = "…"

            cells: TransmissionTableRowCells = (
                escape(eventID),
                escape(station),
                escape(system),
                escape(channel),
                escape(self.dateTimeTextAsDisplayText(startTime)),
                durationCell,
                escape(path),
                sha256Cell,
                escape(transcription),
            )

            rowData: TransmissionTableRowData = (cells, key)
            tableData.append(rowData)

        self._tableData = tuple(tableData)
        self.updateTable()

    def watch_transmissions(self, transmissions: Sequence[TransmissionTuple]) -> None:
        self.log(f"Received {len(self.transmissions)} transmissions")
        try:
            self.updateTransmissions()
        except Exception as e:  # noqa: BLE001
            self.log(f"Unable to update transmissions: {e}")

    def watch_displayKeys(self, displayKeys: frozenset[str]) -> None:
        self.log(f"Received display keys: {displayKeys}")
        try:
            self.updateTable()
        except Exception as e:  # noqa: BLE001
            self.log(f"Unable to update table: {e}")

    @on(DataTable.RowSelected)
    def handle_row_selected(self, message: DataTable.RowSelected) -> None:
        key = message.row_key.value
        assert key is not None
        self.post_message(self.TransmissionSelected(self, key))
