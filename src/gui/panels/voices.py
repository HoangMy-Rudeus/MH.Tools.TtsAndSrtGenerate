"""Voice browser panel — list voices, preview with synthesis, copy name."""

import tempfile
import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ...engines.edge import EdgeTTSEngine, list_voices_sync
from ...models.config import DEFAULT_KOKORO_VOICES
from ..state import AppState
from ..widgets.audio_player import AudioPlayerWidget

_PREVIEW_TEXT = "Hello, this is a preview of this voice."


class VoiceBrowserPanel(ctk.CTkFrame):
    """Browse Edge / Kokoro voices with live synthesis preview."""

    def __init__(self, master, state: AppState, **kwargs):
        super().__init__(master, **kwargs)
        self._state = state
        self._voices: list[dict] = []
        self._selected_voice: Optional[str] = None
        self._preview_tmp: Optional[str] = None

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(top, text="Engine:").pack(side="left", padx=4)
        self._engine_var = ctk.StringVar(value="edge")
        for val in ("edge", "kokoro"):
            ctk.CTkRadioButton(
                top, text=val, variable=self._engine_var, value=val,
                command=self._load_voices,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(top, text="Language:").pack(side="left", padx=(16, 4))
        self._lang_var = ctk.StringVar(value="en")
        self._lang_entry = ctk.CTkEntry(top, textvariable=self._lang_var, width=60)
        self._lang_entry.pack(side="left")
        ctk.CTkButton(top, text="Filter", width=70, command=self._load_voices).pack(
            side="left", padx=4
        )
        self._lbl_loading = ctk.CTkLabel(top, text="")
        self._lbl_loading.pack(side="right", padx=8)

        # Voice list
        self._list_frame = ctk.CTkScrollableFrame(self, label_text="Voices")
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # Bottom: player + buttons
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(4, 8))
        ctk.CTkButton(bottom, text="▶ Preview", command=self._preview).pack(side="left", padx=4)
        ctk.CTkButton(bottom, text="Copy Name", command=self._copy_name).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(bottom, text="")
        self._lbl_msg.pack(side="left", padx=8)
        self._player_widget = AudioPlayerWidget(bottom, player=state.player)
        self._player_widget.pack(side="right", padx=4)

        self._load_voices()

    def _load_voices(self) -> None:
        engine = self._engine_var.get()
        if engine == "kokoro":
            self._voices = [
                {"ShortName": v, "Gender": "–", "Locale": "en"}
                for v in DEFAULT_KOKORO_VOICES.values()
            ]
            self._render_voices()
            return

        # Edge: network call in thread
        self._lbl_loading.configure(text="Loading…")
        lang = self._lang_var.get().strip() or "en"
        threading.Thread(
            target=self._fetch_edge_voices, args=(lang,), daemon=True
        ).start()

    def _fetch_edge_voices(self, lang: str) -> None:
        try:
            voices = list_voices_sync(lang)
        except Exception as exc:
            self.after(0, lambda: self._lbl_loading.configure(text=f"Error: {exc}"))
            return
        self._voices = voices
        self.after(0, self._render_voices)

    def _render_voices(self) -> None:
        self._lbl_loading.configure(text=f"{len(self._voices)} voices")
        for w in self._list_frame.winfo_children():
            w.destroy()
        for voice in self._voices:
            name = voice["ShortName"]
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=name, width=220, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=voice.get("Gender", ""), width=70).pack(side="left")
            ctk.CTkLabel(row, text=voice.get("Locale", ""), width=100).pack(side="left")
            row.bind("<Button-1>", lambda e, n=name: self._select(n))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, n=name: self._select(n))
        if self._voices:
            self._select(self._voices[0]["ShortName"])

    def _select(self, voice_name: str) -> None:
        self._selected_voice = voice_name
        self._lbl_msg.configure(text=f"Selected: {voice_name}")

    def _preview(self) -> None:
        if not self._selected_voice:
            return
        voice = self._selected_voice
        engine_name = self._engine_var.get()
        self._lbl_msg.configure(text="Synthesizing…")
        threading.Thread(
            target=self._synth_preview, args=(voice, engine_name), daemon=True
        ).start()

    def _synth_preview(self, voice: str, engine_name: str) -> None:
        try:
            if engine_name == "kokoro":
                self.after(0, lambda: self._lbl_msg.configure(
                    text="Kokoro preview requires model files — use Edge instead."
                ))
                return
            engine = EdgeTTSEngine()
            result = engine.synthesize(_PREVIEW_TEXT, voice=voice, speed=1.0)
            if not result.success or not result.audio_bytes:
                raise RuntimeError(result.error or "no audio")
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(result.audio_bytes)
            tmp.close()
            self._preview_tmp = tmp.name
            self.after(0, lambda: (
                self._player_widget.load(self._preview_tmp),
                self._player_widget.play(),
                self._lbl_msg.configure(text=""),
            ))
        except Exception as exc:
            self.after(0, lambda: self._lbl_msg.configure(text=f"Preview failed: {exc}"))

    def _copy_name(self) -> None:
        if self._selected_voice:
            self.clipboard_clear()
            self.clipboard_append(self._selected_voice)
            self._lbl_msg.configure(text=f"Copied: {self._selected_voice}")
