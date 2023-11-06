from typing import ClassVar

from textual.widgets import Static


__all__ = ()


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
