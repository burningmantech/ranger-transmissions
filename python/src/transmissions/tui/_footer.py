from typing import ClassVar

from textual.reactive import reactive
from textual.widgets import Static


__all__ = ()


class Footer(Static):
    """
    App footer.
    """

    DEFAULT_CSS: ClassVar[str] = """
        Footer {
            height: 2;
            dock: bottom;
            content-align: center middle;
            color: $text-muted;
            background: $primary-darken-3;
        }
        """

    totalTransmissions = reactive(0)
    displayedTransmissions = reactive(0)
    disclaimer = reactive(
        "Copyright © Burning Man"
        " - Audio and displayed content is confidential and proprietary"
    )

    def on_mount(self) -> None:
        self.updateInfo()

    def updateInfo(self) -> None:
        info = (
            f"{self.displayedTransmissions} of {self.totalTransmissions} transmissions"
        )
        self.update(f"{info}\n{self.disclaimer}")

    def watch_totalTransmissions(self, transmission: str) -> None:
        self.updateInfo()

    def watch_displayedTransmissions(self, transmission: str) -> None:
        self.updateInfo()

    def watch_disclaimer(self, transmission: str) -> None:
        self.updateInfo()
