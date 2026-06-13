"""Library panel — browse, open, duplicate, and delete topic scripts."""

import json
import shutil
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ...models.script import Script
from ...services.validator import ScriptValidator
from ..import_scan import scan_folder
from ..state import AppState


class LibraryPanelLogic:
    """Filesystem logic for LibraryPanel. No Tk dependency."""

    def __init__(self, topics_dir: Path):
        self.topics_dir = topics_dir

    def load(self) -> list[tuple[Path, str, str]]:
        """Return [(path, lesson_id, title)] for every valid script (root + subfolders)."""
        return [
            (f.path, f.lesson_id, f.title)
            for f in scan_folder(self.topics_dir) if f.valid
        ]

    def load_grouped(self) -> list[tuple[str, list[tuple[Path, str, str]]]]:
        """
        Return ``[(category, [(path, lesson_id, title), ...]), ...]``.

        Category is the immediate subfolder name; root-level files use ``""``.
        Root files come first, then categories alphabetically.
        """
        groups: dict[str, list[tuple[Path, str, str]]] = {}
        for f in scan_folder(self.topics_dir):
            if not f.valid:
                continue
            groups.setdefault(f.category, []).append((f.path, f.lesson_id, f.title))
        return sorted(groups.items(), key=lambda kv: (kv[0] != "", kv[0]))

    def import_folder(self, src: str | Path) -> int:
        """
        Copy every ``.json`` script under ``src`` (2 levels) into ``topics_dir``,
        preserving the ``<category>/file.json`` layout. Returns the number copied.
        """
        copied = 0
        for f in scan_folder(src):
            dest_dir = self.topics_dir / f.category if f.category else self.topics_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f.path, dest_dir / f.path.name)
            copied += 1
        return copied

    def duplicate(self, src: Path) -> Path:
        dst = src.parent / f"{src.stem}_copy{src.suffix}"
        shutil.copy2(src, dst)
        return dst

    def delete(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def load_script(self, path: Path) -> Script:
        return ScriptValidator.load_script(path)


class LibraryPanel(ctk.CTkFrame):
    """Two-column script library: file list | read-only preview."""

    def __init__(
        self,
        master,
        state: AppState,
        open_in_editor: Callable[[Script], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._state = state
        topics_dir = Path(state.config.paths.topics_dir)
        self.logic = LibraryPanelLogic(topics_dir)
        self._open_in_editor = open_in_editor
        self._items: list[tuple[Path, str, str]] = []
        self._selected: Optional[int] = None

        # Left: file list
        self._left = ctk.CTkScrollableFrame(self, label_text="Topics", width=240)
        self._left.pack(side="left", fill="y", padx=(8, 4), pady=8)

        # Right: preview + action buttons
        right = ctk.CTkFrame(self)
        right.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(btn_row, text="Open in Editor", command=self._open).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btn_row, text="Duplicate", command=self._duplicate).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btn_row, text="Import Folder", command=self._import_folder).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btn_row, text="Delete", fg_color="#ef4444", hover_color="#dc2626",
                      command=self._delete).pack(side="left", padx=4)
        self._lbl_msg = ctk.CTkLabel(btn_row, text="")
        self._lbl_msg.pack(side="right", padx=8)

        self._preview = ctk.CTkTextbox(right, state="disabled")
        self._preview.pack(fill="both", expand=True, padx=8, pady=4)

        self.refresh()

    def refresh(self) -> None:
        grouped = self.logic.load_grouped()
        self._items = [item for _, items in grouped for item in items]
        for w in self._left.winfo_children():
            w.destroy()
        if not self._items:
            ctk.CTkLabel(
                self._left, text=f"{self.logic.topics_dir} not found or empty"
            ).pack(pady=8)
            return
        flat_index = 0
        for category, items in grouped:
            if category:
                ctk.CTkLabel(
                    self._left, text=category, anchor="w",
                    font=ctk.CTkFont(weight="bold"),
                ).pack(fill="x", pady=(8, 2), padx=4)
            for (path, lesson_id, title) in items:
                btn = ctk.CTkButton(
                    self._left, text=f"{lesson_id}\n{title[:20]}", anchor="w",
                    command=lambda n=flat_index: self._select(n),
                )
                btn.pack(fill="x", pady=1, padx=2)
                flat_index += 1
        self._select(0)

    def _import_folder(self) -> None:
        src = ctk.filedialog.askdirectory(title="Select a folder of scripts to import")
        if not src:
            return
        count = self.logic.import_folder(src)
        self._lbl_msg.configure(text=f"Imported {count} file(s)", text_color="green")
        self.refresh()

    def _select(self, index: int) -> None:
        self._selected = index
        if not (0 <= index < len(self._items)):
            return
        path, lesson_id, title = self._items[index]
        try:
            script = self.logic.load_script(path)
            lines_text = "\n".join(
                f"  {l.id}. [{l.speaker}] {l.text}" for l in script.lines
            )
            preview = (
                f"lesson_id: {script.lesson_id}\n"
                f"title:     {script.title}\n"
                f"language:  {script.language}  level: {script.level}\n\n"
                f"Lines ({len(script.lines)}):\n{lines_text}"
            )
        except Exception as exc:
            preview = f"(Cannot read script: {exc})"
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", preview)
        self._preview.configure(state="disabled")

    def _open(self) -> None:
        if self._selected is None or not self._items:
            return
        path = self._items[self._selected][0]
        try:
            script = self.logic.load_script(path)
            self._open_in_editor(script)
        except Exception as exc:
            self._lbl_msg.configure(text=str(exc), text_color="red")

    def _duplicate(self) -> None:
        if self._selected is None or not self._items:
            return
        copy = self.logic.duplicate(self._items[self._selected][0])
        self._lbl_msg.configure(text=f"Created {copy.name}", text_color="green")
        self.refresh()

    def _delete(self) -> None:
        if self._selected is None or not self._items:
            return
        path, lesson_id, _ = self._items[self._selected]
        dialog = ctk.CTkInputDialog(
            text=f"Type '{lesson_id}' to confirm deletion:", title="Confirm Delete"
        )
        if dialog.get_input() == lesson_id:
            self.logic.delete(path)
            self._selected = None
            self._lbl_msg.configure(text=f"Deleted {path.name}", text_color="orange")
            self.refresh()
