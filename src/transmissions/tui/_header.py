from typing import ClassVar

from textual.widgets import Static


__all__ = ()


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
