"""Config screen: edit engine / voices / language / audio / synthesis params and save."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, TextArea


class ConfigScreen(Screen):
    """Edit configuration and persist it to the YAML config path."""

    BINDINGS = [("escape", "app.pop_screen", "Back"), ("ctrl+s", "save", "Save")]

    def compose(self) -> ComposeResult:
        cfg = self.app.state.config
        yield Header()
        with VerticalScroll(id="config-form"):
            yield Label("Engine")
            yield Select(
                [("edge", "edge"), ("kokoro", "kokoro")],
                value=cfg.engine, id="engine", allow_blank=False,
            )

            yield Label("Audio: sample_rate")
            yield Input(str(cfg.audio.sample_rate), id="sample_rate")
            yield Label("Audio: normalize_to (dBFS)")
            yield Input(str(cfg.audio.normalize_to), id="normalize_to")
            yield Label("Audio: output_format")
            yield Select(
                [("mp3", "mp3"), ("wav", "wav")],
                value=cfg.audio.output_format, id="output_format", allow_blank=False,
            )

            yield Label("Synthesis: default_pause_ms")
            yield Input(str(cfg.synthesis.default_pause_ms), id="default_pause_ms")
            yield Label("Synthesis: initial_silence_ms")
            yield Input(str(cfg.synthesis.initial_silence_ms), id="initial_silence_ms")
            yield Label("Synthesis: max_retries")
            yield Input(str(cfg.synthesis.max_retries), id="max_retries")

            yield Label("Edge voices (one 'speaker_id=voice' per line)")
            yield TextArea(self._voices_text(cfg.edge.voices), id="edge_voices")

            yield Button("Save", id="save-btn", variant="primary")
            yield Static("", id="config-msg")
        yield Footer()

    @staticmethod
    def _voices_text(voices: dict) -> str:
        return "\n".join(f"{k}={v}" for k, v in voices.items())

    @staticmethod
    def _parse_voices(text: str) -> dict:
        out = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
        return out

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()

    def action_save(self) -> None:
        from ..config_io import save_config

        cfg = self.app.state.config
        try:
            cfg.engine = str(self.query_one("#engine", Select).value)
            cfg.audio.sample_rate = int(self.query_one("#sample_rate", Input).value)
            cfg.audio.normalize_to = float(self.query_one("#normalize_to", Input).value)
            cfg.audio.output_format = str(self.query_one("#output_format", Select).value)
            cfg.synthesis.default_pause_ms = int(self.query_one("#default_pause_ms", Input).value)
            cfg.synthesis.initial_silence_ms = int(self.query_one("#initial_silence_ms", Input).value)
            cfg.synthesis.max_retries = int(self.query_one("#max_retries", Input).value)
            cfg.edge.voices = self._parse_voices(self.query_one("#edge_voices", TextArea).text)
            save_config(cfg, self.app.state.config_path)
        except (ValueError, OSError) as exc:
            self.query_one("#config-msg", Static).update(f"Save failed: {exc}")
            return
        self.query_one("#config-msg", Static).update("Saved.")
