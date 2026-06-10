"""Config screen."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class ConfigScreen(Screen):
    """Edit + save configuration. (Filled out in Task 9.)"""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self):
        yield Header()
        yield Static("Config", id="config-placeholder")
        yield Footer()
