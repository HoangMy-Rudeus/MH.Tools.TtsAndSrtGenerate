"""Queue screen (home)."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class QueueScreen(Screen):
    """Lists queued topics and runs them. (Filled out in Task 8.)"""

    def compose(self):
        yield Header()
        yield Static("Queue", id="queue-placeholder")
        yield Footer()
