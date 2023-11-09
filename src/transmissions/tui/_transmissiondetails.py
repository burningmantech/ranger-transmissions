from datetime import datetime as DateTime
from pathlib import Path
from typing import ClassVar

from arrow import get as makeArrow
from rich.markup import escape
from textual.reactive import reactive
from textual.widgets import Static

from ._util import TransmissionTuple, dateTimeFromText, optionalEscape


__all__ = ()


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

        pathAvailable = Path(self.transmission[7]).is_file()

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
            f"([bold yellow]{eventID}[/])"
            f" Station [bold yellow]{station}[/]"
            f" on {system} [bold yellow]{channel}[/]"
            f" {startTime} ({duration}s)"
        )

        if not pathAvailable:
            details.append("[bold red]Audio file is not available[/]")

        if self.showFileInfo:
            if sha256 is None:
                details.append(path)
            else:
                details.append(f"SHA {sha256}: {path}")

        details.append("")

        if transcription is None:
            details.append("[i](transcription not available)[/]")
        else:
            details.append(transcription.strip())

        self.update("\n".join(details))

    def watch_transmission(self, transmission: str) -> None:
        try:
            self.updateDetails()
        except Exception as e:
            self.log(f"Unable to update transmission details: {e}")
