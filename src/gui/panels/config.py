"""Config panel — edit and persist the YAML configuration."""

import customtkinter as ctk

from ...tui.config_io import save_config, load_config
from ..state import AppState


class ConfigPanel(ctk.CTkFrame):
    """Scrollable form: engine, audio, synthesis, voice map. Save / Reset buttons."""

    def __init__(self, master, state: AppState, **kwargs):
        super().__init__(master, **kwargs)
        self._state = state

        # Toolbar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(bar, text="💾 Save", command=self._save).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="↺ Reset", command=self._reset).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(bar, text="")
        self._lbl_msg.pack(side="right", padx=8)

        # Scrollable form
        self._form = ctk.CTkScrollableFrame(self)
        self._form.pack(fill="both", expand=True, padx=8, pady=4)

        self._build_form()

    def _build_form(self) -> None:
        cfg = self._state.config
        for w in self._form.winfo_children():
            w.destroy()

        def _lbl(text):
            ctk.CTkLabel(self._form, text=text, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=4, pady=(10, 2))

        def _row(label, attr, default):
            ctk.CTkLabel(self._form, text=label, anchor="w").pack(fill="x", padx=12, pady=(2, 0))
            e = ctk.CTkEntry(self._form)
            e.insert(0, str(default))
            e.pack(fill="x", padx=12, pady=2)
            setattr(self, attr, e)

        def _folder_row(label, attr, default):
            ctk.CTkLabel(self._form, text=label, anchor="w").pack(fill="x", padx=12, pady=(2, 0))
            row = ctk.CTkFrame(self._form, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            e = ctk.CTkEntry(row)
            e.insert(0, str(default))
            e.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Browse…", width=80,
                command=lambda entry=e: self._browse_into(entry),
            ).pack(side="left", padx=(4, 0))
            setattr(self, attr, e)

        # Folders
        _lbl("Folders")
        _folder_row("topics_dir", "_e_topics_dir", cfg.paths.topics_dir)
        _folder_row("output_dir", "_e_output_dir", cfg.paths.output_dir)
        _folder_row("import_dir  (blank = use topics_dir)", "_e_import_dir", cfg.paths.import_dir)

        # Engine
        _lbl("Engine")
        self._engine_var = ctk.StringVar(value=cfg.engine)
        for val in ("edge", "kokoro"):
            ctk.CTkRadioButton(
                self._form, text=val, variable=self._engine_var, value=val
            ).pack(anchor="w", padx=16, pady=2)

        # Audio
        _lbl("Audio")
        _row("sample_rate", "_e_sample_rate", cfg.audio.sample_rate)
        _row("normalize_to (dBFS)", "_e_normalize", cfg.audio.normalize_to)
        ctk.CTkLabel(self._form, text="output_format", anchor="w").pack(fill="x", padx=12, pady=(2,0))
        self._fmt_var = ctk.StringVar(value=cfg.audio.output_format)
        for val in ("mp3", "wav"):
            ctk.CTkRadioButton(
                self._form, text=val, variable=self._fmt_var, value=val
            ).pack(anchor="w", padx=16, pady=2)

        # Synthesis
        _lbl("Synthesis")
        _row("default_pause_ms", "_e_pause", cfg.synthesis.default_pause_ms)
        _row("initial_silence_ms", "_e_silence", cfg.synthesis.initial_silence_ms)
        _row("max_retries", "_e_retries", cfg.synthesis.max_retries)

        # Edge voice map
        _lbl("Edge voices  (speaker → voice name)")
        self._voice_entries: dict[str, ctk.CTkEntry] = {}
        for speaker, voice in cfg.edge.voices.items():
            row = ctk.CTkFrame(self._form, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=speaker, width=130, anchor="w").pack(side="left")
            e = ctk.CTkEntry(row)
            e.insert(0, voice)
            e.pack(side="left", fill="x", expand=True)
            self._voice_entries[speaker] = e

    def _browse_into(self, entry: ctk.CTkEntry) -> None:
        path = ctk.filedialog.askdirectory(title="Select folder")
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _save(self) -> None:
        cfg = self._state.config
        try:
            cfg.paths.topics_dir = self._e_topics_dir.get().strip()
            cfg.paths.output_dir = self._e_output_dir.get().strip()
            cfg.paths.import_dir = self._e_import_dir.get().strip()
            cfg.engine = self._engine_var.get()
            cfg.audio.sample_rate = int(self._e_sample_rate.get())
            cfg.audio.normalize_to = float(self._e_normalize.get())
            cfg.audio.output_format = self._fmt_var.get()
            cfg.synthesis.default_pause_ms = int(self._e_pause.get())
            cfg.synthesis.initial_silence_ms = int(self._e_silence.get())
            cfg.synthesis.max_retries = int(self._e_retries.get())
            cfg.edge.voices = {
                sp: e.get() for sp, e in self._voice_entries.items()
            }
            save_config(cfg, self._state.config_path)
            self._lbl_msg.configure(text="Saved.", text_color="green")
        except (ValueError, OSError) as exc:
            self._lbl_msg.configure(text=f"Error: {exc}", text_color="red")

    def _reset(self) -> None:
        self._state.config = load_config(self._state.config_path)
        self._build_form()
        self._lbl_msg.configure(text="Reset.")
