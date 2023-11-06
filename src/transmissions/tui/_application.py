from collections.abc import Iterable

from textual.app import App

from transmissions.model import Transmission

from ._transmissionsscreen import TransmissionsScreen


__all__ = ()


def transmissionKey(transmission: Transmission) -> str:
    return ":".join(
        (
            transmission.eventID,
            transmission.system,
            transmission.channel,
            str(transmission.startTime),
        )
    )


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
