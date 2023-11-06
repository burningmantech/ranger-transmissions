from typing import ClassVar

from textual.app import ComposeResult
from textual.widgets import Static

from ._searchfield import SearchField
from ._transmissiondetails import TransmissionDetails
from ._transmissionlist import TransmissionList


__all__ = ()


class Body(Static):
    """
    Container for the application body.
    """

    DEFAULT_CSS: ClassVar[
        str
    ] = """
        Body {
            width: 1fr;
            height: 1fr;
        }
        """

    def compose(self) -> ComposeResult:
        yield SearchField()
        yield TransmissionList(id="TransmissionList")
        yield TransmissionDetails(id="TransmissionDetails")
