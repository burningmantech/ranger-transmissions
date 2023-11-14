from collections.abc import Iterable

from textual.app import App

from transmissions.model import Transmission
from transmissions.search import TransmissionsIndex

from ._transmissionsscreen import TransmissionsScreen


__all__ = ()


class Application(App):
    """
    Transmissions application.
    """

    TITLE = "Transmissions"
    SUB_TITLE = ""

    BINDINGS = [
        ("d", "dark", "Toggle dark mode"),
        ("q", "quit", "Quit application"),
    ]

    def __init__(
        self,
        transmissions: Iterable[Transmission],
        searchIndex: TransmissionsIndex,
    ) -> None:
        self.transmissions = tuple(sorted(transmissions))
        self.searchIndex = searchIndex
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen(
            TransmissionsScreen(self.transmissions, self.searchIndex)
        )

    async def action_quit(self) -> None:
        self.exit()

    async def action_dark(self) -> None:
        self.dark = not self.dark
