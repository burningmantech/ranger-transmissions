from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Placeholder

from transmissions.store import TXDataStore


__all__ = ()


async def interactiveApplication(store: TXDataStore) -> None:
    """
    Run the interactive app.
    """
    TransmissionsApp().run()


class Header(Placeholder):
    """
    App header.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        Header {
            height: 3;
            dock: top;
        }
        """


class Footer(Placeholder):
    """
    App footer.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    Footer {
        height: 3;
        dock: bottom;
    }
    """


class BodyContainer(Placeholder):
    """
    Container for the application body.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    BodyContainer {
        width: 1fr;
        height: 1fr;
        border: solid white;
    }
    """

    def compose(self) -> ComposeResult:
        yield Search(id="Search")
        yield TransmissionList(id="TransmissionList")
        yield TransmissionDetails(id="TransmissionDetails")
        yield EventNavigation(id="Events")


class EventNavigation(Placeholder):
    """
    App footer.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    EventNavigation {
        width: 20;
        dock: left;
    }
    """


class Search(Placeholder):
    """
    Search field.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    Search {
        height: 3;
        dock: top;
    }
    """


class TransmissionList(VerticalScroll):
    """
    List of transmissions.
    """

    def compose(self) -> ComposeResult:
        for i in range(100):
            yield TransmissionListItem(id=f"TX {i}")


class TransmissionListItem(Placeholder):
    """
    Transmission item in list.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    TransmissionListItem {
        height: 1;
    }
    """


class TransmissionDetails(Placeholder):
    """
    Search field.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
    TransmissionDetails {
        height: 3;
        dock: bottom;
    }
    """


class TransmissionsScreen(Screen):
    """
    Transmissions screen.
    """

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        yield Footer(id="Footer")
        yield BodyContainer(id="Body")


class TransmissionsApp(App):
    """
    Transmissions application.
    """

    def on_mount(self) -> None:
        self.push_screen(TransmissionsScreen())
