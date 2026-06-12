"""Editor panel — author a conversation script line by line."""

from pathlib import Path
from typing import Callable, Optional

from ...models.script import Script, ScriptLine, ScriptSettings
from ...services.validator import ScriptValidator, ValidationError
from ...tui.script_io import save_script
from ..state import AppState

EMOTIONS = ["neutral", "friendly", "cheerful", "serious", "excited"]


class EditorPanelLogic:
    """State-mutation logic for the Editor panel. No Tk dependency."""

    def __init__(self, state: AppState):
        self.state = state
        self.lines: list[ScriptLine] = []

    def _next_id(self) -> int:
        return (max((l.id for l in self.lines), default=0)) + 1

    def load_script(self, script: Script) -> None:
        self.lines = list(script.lines)

    def move_up(self, index: int) -> bool:
        if index <= 0 or index >= len(self.lines):
            return False
        self.lines[index - 1], self.lines[index] = self.lines[index], self.lines[index - 1]
        return True

    def move_down(self, index: int) -> bool:
        if index < 0 or index >= len(self.lines) - 1:
            return False
        self.lines[index + 1], self.lines[index] = self.lines[index], self.lines[index + 1]
        return True

    def save(
        self,
        lesson_id: str,
        title: str,
        language: str,
        level: str,
        on_save: Callable[[], None],
    ) -> tuple[bool, str]:
        """Validate and save. Returns (success, message)."""
        script = Script(
            lesson_id=lesson_id.strip(),
            title=title.strip(),
            lines=self.lines,
            language=language.strip() or "en",
            level=level.strip() or "B1",
            settings=ScriptSettings(),
        )
        try:
            ScriptValidator().validate_or_raise(script)
        except ValidationError as exc:
            return False, str(exc)
        path = Path("topics") / f"{script.lesson_id}.json"
        save_script(script, path)
        on_save()
        return True, f"Saved {path}"


class EditorPanel:
    """Two-column script editor: metadata + line list | line form.

    The Tk/CTk rendering is a separate concern; import customtkinter lazily
    so this module can be imported in headless test environments without a
    display.
    """

    def __init__(
        self,
        master,
        state: AppState,
        on_save: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        import customtkinter as ctk
        from ..widgets.line_form import LineFormDialog, SPEAKERS

        ctk.CTkFrame.__init__(self, master, **kwargs)
        self.logic = EditorPanelLogic(state)
        self._on_save = on_save or (lambda: None)
        self._selected: Optional[int] = None
        self._LineFormDialog = LineFormDialog
        self._SPEAKERS = SPEAKERS
        self._ctk = ctk

        # ── Left column ──────────────────────────────────────────
        left = ctk.CTkFrame(self)
        left.place(relx=0, rely=0, relwidth=0.40, relheight=1.0)

        for label, attr in [("lesson_id", "_e_lid"), ("title", "_e_title"),
                             ("language", "_e_lang"), ("level", "_e_level")]:
            ctk.CTkLabel(left, text=label, anchor="w").pack(fill="x", padx=8, pady=(4, 0))
            entry = ctk.CTkEntry(left)
            entry.pack(fill="x", padx=8)
            setattr(self, attr, entry)

        ctk.CTkLabel(left, text="Lines", anchor="w").pack(fill="x", padx=8, pady=(8, 0))
        self._line_scroll = ctk.CTkScrollableFrame(left)
        self._line_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        # ── Right column ─────────────────────────────────────────
        right = ctk.CTkFrame(self)
        right.place(relx=0.40, rely=0, relwidth=0.60, relheight=1.0)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=8)
        for text, cmd in [
            ("Add",      self._add_line),
            ("Delete",   self._delete_line),
            ("Up",       self._move_up),
            ("Down",     self._move_down),
            ("Save",     self._save),
        ]:
            ctk.CTkButton(btn_row, text=text, command=cmd, width=80).pack(
                side="left", padx=2
            )

        self._lbl_msg = ctk.CTkLabel(right, text="")
        self._lbl_msg.pack(padx=8, pady=4)

        self._refresh_lines()

    # ── public ────────────────────────────────────────────────────

    def load_script(self, script: Script) -> None:
        self.logic.load_script(script)
        self._e_lid.delete(0, "end"); self._e_lid.insert(0, script.lesson_id)
        self._e_title.delete(0, "end"); self._e_title.insert(0, script.title)
        self._e_lang.delete(0, "end"); self._e_lang.insert(0, script.language)
        self._e_level.delete(0, "end"); self._e_level.insert(0, script.level)
        self._refresh_lines()

    # ── private ───────────────────────────────────────────────────

    def _refresh_lines(self) -> None:
        ctk = self._ctk
        for w in self._line_scroll.winfo_children():
            w.destroy()
        for i, line in enumerate(self.logic.lines):
            preview = line.text[:35] + ("..." if len(line.text) > 35 else "")
            row = ctk.CTkFrame(self._line_scroll)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{line.id}", width=30).pack(side="left")
            ctk.CTkLabel(row, text=line.speaker, width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=preview, anchor="w").pack(side="left", fill="x", expand=True)
            idx = i
            row.bind("<Button-1>", lambda e, n=idx: self._select(n))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, n=idx: self._select(n))

    def _select(self, index: int) -> None:
        self._selected = index

    def _add_line(self) -> None:
        new = ScriptLine(id=self.logic._next_id(), speaker=self._SPEAKERS[0], text="")
        dlg = self._LineFormDialog(self, new)
        self.wait_window(dlg)
        if dlg.result:
            self.logic.lines.append(dlg.result)
            self._refresh_lines()

    def _delete_line(self) -> None:
        if self._selected is not None and 0 <= self._selected < len(self.logic.lines):
            del self.logic.lines[self._selected]
            self._selected = None
            self._refresh_lines()

    def _move_up(self) -> None:
        if self._selected is not None and self.logic.move_up(self._selected):
            self._selected -= 1
            self._refresh_lines()

    def _move_down(self) -> None:
        if self._selected is not None and self.logic.move_down(self._selected):
            self._selected += 1
            self._refresh_lines()

    def _save(self) -> None:
        ok, msg = self.logic.save(
            self._e_lid.get(), self._e_title.get(),
            self._e_lang.get(), self._e_level.get(),
            on_save=self._on_save,
        )
        color = "green" if ok else "red"
        self._lbl_msg.configure(text=msg, text_color=color)
