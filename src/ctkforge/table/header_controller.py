"""Reacts to the mouse on the table header: hover highlights, click sorting, divider dragging, and auto-fit."""

import tkinter as tk
from bisect import bisect_right
from collections.abc import Callable
from typing import Any

from ctkforge.geometry import scale
from ctkforge.table.column_layout import ColumnLayoutManager, ScopedDictNormalizer
from ctkforge.table.column_resizer import ColumnResizer
from ctkforge.table.constants import DIVIDER_HOVER_TOLERANCE, MIN_COLUMN_WIDTH
from ctkforge.table.data_model import TableDataModel

__all__ = ["HeaderController"]


class HeaderController:
    """Owns header interaction state and turns mouse events on the header into table actions."""

    def __init__(
        self,
        widget: Any,
        header_canvas: tk.Canvas,
        data_model: TableDataModel,
        layout_mgr: ColumnLayoutManager,
        *,
        header_sortable: bool | dict[int | str, bool],
        normalize_scoped_dict: ScopedDictNormalizer,
        is_header_visible: Callable[[], bool],
        has_hover_color: Callable[[], bool],
        get_canvas_width: Callable[[], int],
        get_scroll_x: Callable[[], float],
        sort_by: Callable[[int, bool], None],
        clear_sort: Callable[[], None],
        redraw_header: Callable[[], None],
        redraw: Callable[[], None],
    ) -> None:
        """Wire the controller to the table through shared collaborators and plain callbacks.

        Args:
            widget: The table widget, used only to read the DPI scaling factor.
            header_canvas: The canvas the header is drawn on. Its mouse cursor is changed here.
            data_model: Source of the current sort column and direction.
            layout_mgr: Provides column geometry and applies resized or auto-fitted widths.
            header_sortable: Initial rules for which headers sort on click (a bool or a scoped dict).
            normalize_scoped_dict: Splits a scoped dict into its default and per-column values.
            is_header_visible: Returns whether the header bar is currently shown.
            has_hover_color: Returns whether a header hover highlight color is set.
            get_canvas_width: Returns the current body canvas width in pixels.
            get_scroll_x: Returns how far the table is scrolled sideways, in pixels.
            sort_by: Sorts the table by a column, ascending or descending.
            clear_sort: Restores the original row order.
            redraw_header: Repaints only the header.
            redraw: Repaints the whole table.
        """
        self._widget = widget
        self._header_canvas = header_canvas
        self._data_model = data_model
        self._layout_mgr = layout_mgr
        self._normalize_scoped_dict = normalize_scoped_dict
        self._is_header_visible = is_header_visible
        self._has_hover_color = has_hover_color
        self._get_canvas_width = get_canvas_width
        self._get_scroll_x = get_scroll_x
        self._sort_by = sort_by
        self._clear_sort = clear_sort
        self._redraw_header = redraw_header
        self._redraw = redraw

        self._column_resizer = ColumnResizer()
        self._hovered_col: int | None = None
        self._current_cursor: str = ""

        self._sortable_default: bool = True
        self._sortable_cols: dict[int, bool] = {}
        self._raw_sortable: bool | dict[int | str, bool] = header_sortable
        self.set_sortable_rules(header_sortable)

    @property
    def hovered_col(self) -> int | None:
        """Return the visible column index under the pointer, or None when nothing is highlighted."""
        return self._hovered_col

    @property
    def current_cursor(self) -> str:
        """Return the mouse cursor name currently shown over the header ('' means the default arrow)."""
        return self._current_cursor

    @property
    def column_resizer(self) -> ColumnResizer:
        """Return the helper that tracks divider hover and drag-resize state."""
        return self._column_resizer

    def bind_events(self) -> None:
        """Attach the header mouse handlers to the header canvas."""
        self._header_canvas.bind("<Motion>", self.on_motion)
        self._header_canvas.bind("<Button-1>", self.on_click)
        self._header_canvas.bind("<B1-Motion>", self.on_drag)
        self._header_canvas.bind("<ButtonRelease-1>", self.on_release)
        self._header_canvas.bind("<Double-Button-1>", self.on_double_click)
        self._header_canvas.bind("<Triple-Button-1>", self.on_double_click)
        self._header_canvas.bind("<Leave>", self.on_leave)

    # -------------------------------------------------------------------------
    # Sortable Rules
    # -------------------------------------------------------------------------

    @property
    def sortable_setting(self) -> bool | dict[int | str, bool]:
        """Return the sortable rules as a single bool, or a dict that includes a 'default' entry."""
        if not self._sortable_cols:
            return self._sortable_default
        result: dict[int | str, bool] = dict(self._sortable_cols)
        result["default"] = self._sortable_default
        return result

    def set_sortable_rules(self, header_sortable: bool | dict[int | str, bool]) -> None:
        """Apply new sortable rules, keeping the current baseline when a dict omits 'default'."""
        self._raw_sortable = header_sortable
        if isinstance(header_sortable, dict):
            default_val, resolved = self._normalize_scoped_dict(header_sortable)
            if default_val is not None:
                self._sortable_default = bool(default_val)
            for col, is_sortable in resolved.items():
                self._sortable_cols[col] = bool(is_sortable)
        else:
            self._sortable_default = bool(header_sortable)
            self._sortable_cols.clear()

    def reapply_sortable_rules(self) -> None:
        """Resolve the stored sortable rules again, so header title keys follow renamed headers."""
        self.set_sortable_rules(self._raw_sortable)

    def is_column_sortable(self, col: int) -> bool:
        """Check whether clicking this column header is allowed to sort the table."""
        return self._sortable_cols.get(col, self._sortable_default)

    # -------------------------------------------------------------------------
    # Mouse Handlers
    # -------------------------------------------------------------------------

    def on_motion(self, event: Any) -> None:
        """Update the cursor and hover highlight to match the pointer position."""
        if not self._is_header_visible():
            return

        visible_cols = self._layout_mgr.get_visible_columns()
        _, col_offsets = self._layout_mgr.calculate_geometry(self._get_canvas_width())
        logical_x = event.x + self._get_scroll_x()
        divider_tol = scale(self._widget, DIVIDER_HOVER_TOLERANCE)

        matched = self._column_resizer.check_divider_hover(logical_x, col_offsets, divider_tol)
        if matched is not None:
            self._set_cursor("sb_h_double_arrow")
            self._set_hovered_col(None)
        elif not self._column_resizer.is_resizing:
            visible_pos = bisect_right(col_offsets, logical_x) - 1
            is_sortable = 0 <= visible_pos < len(visible_cols) and self.is_column_sortable(visible_cols[visible_pos])
            self._set_cursor("hand2" if is_sortable else "")

            if self._has_hover_color():
                self._set_hovered_col(visible_pos if is_sortable else None)
            else:
                self._set_hovered_col(None)

    def on_leave(self, _event: Any) -> None:
        """Clear the hover highlight and restore the arrow cursor when the pointer leaves the header."""
        self._set_cursor("")
        self._column_resizer.clear_hover()
        self._set_hovered_col(None)

    def on_click(self, event: Any) -> None:
        """Start dragging a column divider, or sort the column whose header was clicked."""
        visible_cols = self._layout_mgr.get_visible_columns()
        col_widths, col_offsets = self._layout_mgr.calculate_geometry(self._get_canvas_width())

        divider = self._column_resizer.hover_divider_col
        if divider is not None:
            self._column_resizer.start_resize(visible_cols[divider - 1], event.x, col_widths[divider - 1])
            return

        clicked_pos = bisect_right(col_offsets, event.x + self._get_scroll_x()) - 1
        if 0 <= clicked_pos < len(visible_cols):
            clicked_col = visible_cols[clicked_pos]
            if self.is_column_sortable(clicked_col):
                self._toggle_sort(clicked_col)

    def on_drag(self, event: Any) -> None:
        """Resize the column being dragged to follow the mouse."""
        resizing_col = self._column_resizer.resizing_col
        if resizing_col is None:
            return

        min_col_w = scale(self._widget, MIN_COLUMN_WIDTH)
        new_width = self._column_resizer.calculate_drag_width(event.x, min_col_w)
        self._layout_mgr.set_column_width(resizing_col, new_width)
        self._redraw()

    def on_release(self, event: Any = None) -> None:
        """Finish any column resize and refresh the hover state under the pointer."""
        if self._column_resizer.is_resizing:
            self._column_resizer.end_resize()
        if event is not None and hasattr(event, "x"):
            self.on_motion(event)
        else:
            self._set_cursor("")

    def on_double_click(self, event: Any = None) -> None:
        """Fit a column to its content when its divider is double-clicked, or sort when the header body is."""
        visible_cols = self._layout_mgr.get_visible_columns()
        _, col_offsets = self._layout_mgr.calculate_geometry(self._get_canvas_width())
        divider_tol = scale(self._widget, max(DIVIDER_HOVER_TOLERANCE * 2, 8))
        has_position = event is not None and hasattr(event, "x")
        logical_x = (event.x + self._get_scroll_x()) if has_position else None

        divider = self._column_resizer.hover_divider_col
        if divider is None and logical_x is not None:
            divider = self._column_resizer.check_divider_hover(logical_x, col_offsets, divider_tol)

        if divider is not None:
            self._column_resizer.end_resize()
            self._layout_mgr.auto_fit_column(visible_cols[divider - 1])
            if has_position:
                self.on_motion(event)
        elif event is not None:
            # Rapid repeated clicks on the header body count as extra sort clicks
            self.on_click(event)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _toggle_sort(self, col: int) -> None:
        """Cycle a column through ascending, descending, and unsorted."""
        if self._data_model.sort_column != col:
            self._sort_by(col, True)
        elif self._data_model.sort_ascending:
            self._sort_by(col, False)
        else:
            self._clear_sort()

    def _set_cursor(self, cursor: str) -> None:
        """Change the header mouse cursor only when the requested one differs from the current one."""
        if self._current_cursor != cursor:
            self._current_cursor = cursor
            self._header_canvas.configure(cursor=cursor)

    def _set_hovered_col(self, col: int | None) -> None:
        """Change the highlighted header column and repaint the header only when it actually changes."""
        if self._hovered_col != col:
            self._hovered_col = col
            self._redraw_header()
