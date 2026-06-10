"""History screen."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class HistoryScreen(Screen):
    """Lists past runs. (Filled out in Task 10.)"""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self):
        yield Header()
        yield Static("History", id="history-placeholder")
        yield Footer()
