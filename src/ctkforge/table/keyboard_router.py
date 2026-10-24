"""Turns keyboard presses on the table body into focus moves, selections, edits, and copying."""

import tkinter as tk
from collections.abc import Callable
from typing import Any

from ctkforge.table.column_layout import ColumnLayoutManager
from ctkforge.table.constants import TK_SHIFT_MASK
from ctkforge.table.data_model import TableDataModel
from ctkforge.table.selection_manager import SelectionManager

__all__ = ["KeyboardRouter"]


class KeyboardRouter:
    """Listens for key presses on the table canvas and carries out the matching table action."""

    def __init__(
        self,
        data_model: TableDataModel,
        selection_manager: SelectionManager,
        layout_mgr: ColumnLayoutManager,
        *,
        get_page_row_count: Callable[[], int],
        is_editing: Callable[[], bool],
        is_copyable: Callable[[], bool],
        scroll_to: Callable[[int | None, int | None], None],
        start_editing: Callable[[int, int], None],
        cancel_edit: Callable[[], None],
        select_all: Callable[[], None],
        clear_selection: Callable[[], None],
        copy_selection: Callable[[], object],
        notify_selection_changed: Callable[[], None],
        redraw: Callable[[], None],
    ) -> None:
        """Wire the router to the table through shared collaborators and plain callbacks.

        Args:
            data_model: Source of the current row count.
            selection_manager: Tracks the focused cell and applies keyboard selections.
            layout_mgr: Tells which columns are visible, so focus skips hidden ones.
            get_page_row_count: Returns how many whole rows fit on screen, at least one.
            is_editing: Returns whether a cell editor is open.
            is_copyable: Returns whether Ctrl+C is allowed to copy.
            scroll_to: Scrolls so the given row and column are visible.
            start_editing: Opens the cell editor at the given row and column.
            cancel_edit: Closes the cell editor and discards its text.
            select_all: Selects every row or cell.
            clear_selection: Clears the selection and the focus ring.
            copy_selection: Copies the selection to the clipboard.
            notify_selection_changed: Calls the user's selection callback.
            redraw: Repaints the table.
        """
        self._data_model = data_model
        self._selection_manager = selection_manager
        self._layout_mgr = layout_mgr
        self._get_page_row_count = get_page_row_count
        self._is_editing = is_editing
        self._is_copyable = is_copyable
        self._scroll_to = scroll_to
        self._start_editing = start_editing
        self._cancel_edit = cancel_edit
        self._select_all = select_all
        self._clear_selection = clear_selection
        self._copy_selection = copy_selection
        self._notify_selection_changed = notify_selection_changed
        self._redraw = redraw

    def bind_to(self, canvas: tk.Canvas) -> None:
        """Attach every keyboard shortcut the table supports to the given canvas."""
        canvas.bind("<Up>", lambda e: self._navigate_focus(-1, 0, e))
        canvas.bind("<Down>", lambda e: self._navigate_focus(1, 0, e))
        canvas.bind("<Left>", lambda e: self._navigate_focus(0, -1, e))
        canvas.bind("<Right>", lambda e: self._navigate_focus(0, 1, e))
        canvas.bind("<Return>", self._on_enter_key)
        canvas.bind("<Prior>", self._on_page_up)
        canvas.bind("<Next>", self._on_page_down)
        canvas.bind("<Home>", self._on_home)
        canvas.bind("<End>", self._on_end)
        canvas.bind("<Control-a>", self._on_select_all)
        canvas.bind("<Control-c>", self._on_copy_shortcut)
        canvas.bind("<space>", self._on_space)
        canvas.bind("<Escape>", self._on_escape_key)

    def _navigate_focus(self, delta_row: int, delta_col: int, event: Any) -> str:
        """Move keyboard focus by row and column offsets and slide the view if needed."""
        if self._data_model.row_count == 0:
            return "break"

        visible_cols = self._layout_mgr.get_visible_columns()
        if not visible_cols:
            return "break"

        is_shift = bool(event.state & TK_SHIFT_MASK)
        total_rows = self._data_model.row_count
        focused_row = self._selection_manager.focused_row
        focused_col = self._selection_manager.focused_col

        cur_r = focused_row if focused_row is not None else 0
        new_r = max(0, min(total_rows - 1, cur_r + delta_row))

        cur_c = focused_col if focused_col is not None else visible_cols[0]
        cur_v = visible_cols.index(cur_c) if cur_c in visible_cols else 0
        new_v = max(0, min(len(visible_cols) - 1, cur_v + delta_col))
        new_c = visible_cols[new_v]

        use_shift = is_shift and self._selection_manager.mode == "extended"
        self._selection_manager.apply_click(new_r, new_c, is_ctrl=False, is_shift=use_shift)

        scroll_c = new_c if self._selection_manager.target == "cell" else None
        self._scroll_to(new_r, scroll_c)
        self._notify_selection_changed()
        self._redraw()
        return "break"

    def _on_enter_key(self, _event: Any) -> str:
        """Start editing the focused cell when Enter is pressed, if its column allows editing."""
        focused_r = self._selection_manager.focused_row
        focused_c = self._selection_manager.focused_col
        if focused_r is not None and focused_c is not None:
            self._start_editing(focused_r, focused_c)
        return "break"

    def _on_page_up(self, event: Any) -> str:
        """Jump focus up by one full screen page of rows."""
        return self._navigate_focus(-self._get_page_row_count(), 0, event)

    def _on_page_down(self, event: Any) -> str:
        """Jump focus down by one full screen page of rows."""
        return self._navigate_focus(self._get_page_row_count(), 0, event)

    def _on_home(self, event: Any) -> str:
        """Jump focus straight to the first row."""
        if self._data_model.row_count == 0:
            return "break"
        cur_row = self._selection_manager.focused_row or 0
        return self._navigate_focus(-cur_row, 0, event)

    def _on_end(self, event: Any) -> str:
        """Jump focus straight to the last row."""
        if self._data_model.row_count == 0:
            return "break"
        cur_row = self._selection_manager.focused_row or 0
        last_row = self._data_model.row_count - 1
        return self._navigate_focus(last_row - cur_row, 0, event)

    def _on_select_all(self, _event: Any) -> str:
        """Select every row or cell when Ctrl+A is pressed."""
        self._select_all()
        return "break"

    def _on_space(self, _event: Any) -> str:
        """Toggle selection on the focused item when the Space bar is pressed."""
        focused_r = self._selection_manager.focused_row
        if focused_r is not None and self._selection_manager.mode in ("single", "extended"):
            focused_c = self._selection_manager.focused_col or 0
            self._selection_manager.apply_click(focused_r, focused_c, is_ctrl=True, is_shift=False)
            self._notify_selection_changed()
            self._redraw()
        return "break"

    def _on_escape_key(self, _event: Any) -> None:
        """Cancel any active cell edit or clear the current selection when Escape is pressed."""
        if self._is_editing():
            self._cancel_edit()
        else:
            self._clear_selection()

    def _on_copy_shortcut(self, _event: Any = None) -> None:
        """Copy selected items to the clipboard when Ctrl+C is pressed."""
        if self._is_copyable():
            self._copy_selection()
