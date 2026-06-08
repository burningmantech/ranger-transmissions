from collections.abc import Iterable
from typing import ClassVar

from textual.app import App

from transmissions.model import Transmission
from transmissions.search import TransmissionsIndex

from ._transmissionsscreen import TransmissionsScreen


__all__ = ()


class Application(App):
    """
    Transmissions application.
    """

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit application"),
    ]

    TITLE = "Transmissions"
    SUB_TITLE = ""

    def __init__(
        self,
        transmissions: Iterable[Transmission],
        searchIndex: TransmissionsIndex,
    ) -> None:
        self.transmissions = tuple(sorted(transmissions))
        self.searchIndex = searchIndex
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen(TransmissionsScreen(self.transmissions, self.searchIndex))

    async def action_quit(self) -> None:
        self.exit()
