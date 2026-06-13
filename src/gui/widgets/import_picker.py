"""Modal dialog: pick scanned scripts (2-level, category → file) to add to the queue."""

from pathlib import Path

import customtkinter as ctk

from ..import_scan import ScannedFile


class ImportPickerDialog(ctk.CTkToplevel):
    """
    Shows scanned files grouped by category with a checkbox each.

    Files already in history are shown disabled with a "✓ done" tag; invalid
    files are greyed out with their error. After the dialog closes,
    ``selected`` holds the chosen :class:`Path` objects (empty if cancelled).
    """

    def __init__(self, master, files: list[ScannedFile], **kwargs):
        super().__init__(master, **kwargs)
        self.title("Import from folder")
        self.geometry("560x520")
        self.selected: list[Path] = []
        self._vars: list[tuple[ScannedFile, ctk.BooleanVar]] = []

        if not files:
            ctk.CTkLabel(self, text="No .json scripts found in the import folder.").pack(
                expand=True, padx=20, pady=20
            )
        else:
            self._build_list(files)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(bar, text="Add Selected", command=self._confirm).pack(side="right", padx=4)
        ctk.CTkButton(
            bar, text="Cancel", fg_color="transparent",
            command=self._cancel,
        ).pack(side="right", padx=4)

        self.transient(master)
        self.grab_set()

    def _build_list(self, files: list[ScannedFile]) -> None:
        scroll = ctk.CTkScrollableFrame(self, label_text="Select scripts to queue")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        groups: dict[str, list[ScannedFile]] = {}
        for f in files:
            groups.setdefault(f.category, []).append(f)

        for category in sorted(groups, key=lambda c: (c != "", c)):
            header = category or "Uncategorized"
            ctk.CTkLabel(
                scroll, text=header, anchor="w",
                font=ctk.CTkFont(weight="bold"),
            ).pack(fill="x", padx=4, pady=(10, 2))
            for f in groups[category]:
                self._add_checkbox(scroll, f)

    def _add_checkbox(self, parent, f: ScannedFile) -> None:
        var = ctk.BooleanVar(value=False)
        label = f"{f.lesson_id}  —  {f.title}" if f.title else f.lesson_id
        if not f.valid:
            label = f"{f.path.name}  (invalid: {f.error})"
        elif f.already_done:
            label = f"{label}   ✓ done"
        cb = ctk.CTkCheckBox(parent, text=label, variable=var)
        cb.pack(anchor="w", padx=20, pady=1)
        if f.already_done or not f.valid:
            cb.configure(state="disabled")
        else:
            self._vars.append((f, var))

    def _confirm(self) -> None:
        self.selected = [f.path for f, var in self._vars if var.get()]
        self.grab_release()
        self.destroy()

    def _cancel(self) -> None:
        self.selected = []
        self.grab_release()
        self.destroy()
