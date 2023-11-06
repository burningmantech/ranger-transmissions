from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


__all__ = ()


class SearchField(Static):
    """
    Search field.
    """

    class QueryUpdated(Message):
        """
        Search field updated message.
        """

        def __init__(self, control: Widget, query: str):
            self._control = control
            self.query = query
            super().__init__()

        @property
        def control(self) -> Widget:
            return self._control

    def compose(self) -> ComposeResult:
        yield Input(
            id="SearchField",
            placeholder=" \N{right-pointing magnifying glass} Search...",
        )

    @on(Input.Submitted)
    def handle_update(self, message: Input.Changed) -> None:
        query = message.value
        self.post_message(self.QueryUpdated(self, query))
