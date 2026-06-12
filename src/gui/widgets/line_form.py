"""Modal dialog to add or edit a single script line."""

from typing import Optional

import customtkinter as ctk

from ...models.script import ScriptLine

EMOTIONS = ["neutral", "friendly", "cheerful", "serious", "excited"]
SPEAKERS = [
    "female_us_1", "female_us_2",
    "male_us_1", "male_us_2",
    "female_uk_1", "male_uk_1",
]


class LineFormDialog(ctk.CTkToplevel):
    """Modal form for a ScriptLine. After wait_window(), read .result."""

    def __init__(self, master, line: ScriptLine):
        super().__init__(master)
        self.title("Edit Line")
        self.resizable(False, False)
        self.grab_set()
        self.result: Optional[ScriptLine] = None
        self._line = line

        fields = [
            ("Speaker", "_speaker", "option", SPEAKERS, line.speaker),
            ("Text", "_text", "entry", None, line.text),
            ("Emotion", "_emotion", "option", EMOTIONS, line.emotion),
            ("pause_after_ms", "_pause", "entry", None, str(line.pause_after_ms)),
            ("speech_rate", "_rate", "entry", None, str(line.speech_rate)),
        ]

        for row, (label, attr, kind, values, default) in enumerate(fields):
            ctk.CTkLabel(self, text=label, anchor="w").grid(
                row=row, column=0, padx=12, pady=4, sticky="w"
            )
            if kind == "option":
                widget = ctk.CTkOptionMenu(self, values=values, width=240)
                widget.set(default)
            else:
                widget = ctk.CTkEntry(self, width=240)
                widget.insert(0, default)
            widget.grid(row=row, column=1, padx=12, pady=4)
            setattr(self, attr, widget)

        self._err = ctk.CTkLabel(self, text="", text_color="red")
        self._err.grid(row=len(fields), column=0, columnspan=2, padx=12, pady=2)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text="OK", command=self._ok, width=90).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, width=90).pack(
            side="left", padx=8
        )

    def _ok(self) -> None:
        try:
            self.result = ScriptLine(
                id=self._line.id,
                speaker=self._speaker.get(),
                text=self._text.get(),
                emotion=self._emotion.get(),
                pause_after_ms=int(self._pause.get()),
                speech_rate=float(self._rate.get()),
            )
        except ValueError as exc:
            self._err.configure(text=str(exc))
            return
        self.destroy()
