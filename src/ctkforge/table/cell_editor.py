"""Manages a single floating CTkEntry text box positioned over an individual cell during in-place editing.

Creates the temporary text box, handles keyboard keys like Enter and Escape,
commits or cancels cell edits, and cleanly destroys the input box when editing finishes.
"""

import tkinter as tk
from collections.abc import Callable
from contextlib import suppress
from typing import Any, Literal

import customtkinter as ctk

from ctkforge.table.constants import EDITOR_BORDER_WIDTH


class CellEditor:
    """Manages the lifecycle, bindings, and teardown of the floating CTkEntry cell editor."""

    def __init__(
        self,
        canvas: tk.Canvas,
        on_commit: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Initialize editor state and callback hooks."""
        self._canvas: tk.Canvas = canvas
        self._on_commit: Callable[[], None] = on_commit
        self._on_cancel: Callable[[], None] = on_cancel

        self._entry: ctk.CTkEntry | None = None
        self._window_id: int | None = None
        self._editing_cell: tuple[int, int] | None = None

    @property
    def is_editing(self) -> bool:
        """Return True if an in-place cell editor is currently active."""
        return self._entry is not None and self._editing_cell is not None

    @property
    def editing_cell(self) -> tuple[int, int] | None:
        """Return (display_row, col_index) of the cell currently being edited."""
        return self._editing_cell

    def start_editing(
        self,
        display_row: int,
        col_index: int,
        initial_value: str,
        x_left: float,
        y_top: float,
        width: int,
        height: int,
        font: tuple[str, int] | ctk.CTkFont,
        border_color: str,
        justify: Literal["left", "center", "right"] = "left",
    ) -> None:
        """Spawn a floating CTkEntry precisely positioned over the target cell."""
        if self._entry is not None:
            self._on_commit()

        self._editing_cell = (display_row, col_index)

        # Match text alignment to the target column setting
        self._entry = ctk.CTkEntry(
            self._canvas,
            width=width,
            height=height,
            font=font,
            justify=justify,
            corner_radius=0,
            border_width=EDITOR_BORDER_WIDTH,
            border_color=border_color,
        )
        self._entry.insert(0, initial_value)
        self._entry.select_range(0, "end")

        self._entry.bind("<Return>", lambda _e: self._on_commit())
        self._entry.bind("<Escape>", lambda _e: self._on_cancel())
        self._entry.bind("<FocusOut>", lambda _e: self._on_commit())

        self._window_id = self._canvas.create_window(
            x_left,
            y_top,
            window=self._entry,
            anchor="nw",
            width=width,
            height=height,
            tags="transient_editor",
        )

        with suppress(tk.TclError):
            self._entry.focus_set()

    def get_text(self) -> str:
        """Read current text from the active editor entry."""
        if self._entry is None:
            return ""
        try:
            return self._entry.get()
        except (tk.TclError, AttributeError):
            return ""

    def destroy_editor(self) -> None:
        """Unbind events and cleanly destroy floating CTkEntry without leaking Tk callbacks."""
        entry = self._entry
        self._entry = None
        self._editing_cell = None

        if entry is not None:
            with suppress(tk.TclError):
                entry.unbind("<FocusOut>")
                entry.unbind("<Return>")
                entry.unbind("<Escape>")
            self._canvas.after_idle(self._safe_destroy_widget, entry)

        if self._window_id is not None:
            with suppress(tk.TclError):
                self._canvas.delete(self._window_id)
            self._window_id = None

    @staticmethod
    def _safe_destroy_widget(widget: Any) -> None:
        """Destroy a widget safely, ignoring teardown errors if already destroyed."""
        with suppress(tk.TclError, AttributeError, RuntimeError):
            widget.destroy()
