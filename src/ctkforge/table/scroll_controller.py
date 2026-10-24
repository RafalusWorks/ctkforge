"""Tracks how far the table is scrolled and keeps the scrollbars, mouse wheel, and scroll requests in sync."""

import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from ctkforge.geometry import scale
from ctkforge.table.column_layout import ColumnLayoutManager
from ctkforge.table.constants import (
    HORIZONTAL_SCROLL_STEP_PX,
    MOUSEWHEEL_BASE_DELTA,
    MOUSEWHEEL_STEP_ROWS,
)
from ctkforge.table.data_model import TableDataModel

__all__ = ["ScrollController"]


class ScrollController:
    """Owns the table's scroll position and applies every kind of scroll request to it."""

    def __init__(
        self,
        widget: Any,
        table_canvas: tk.Canvas,
        header_canvas: tk.Canvas,
        v_scrollbar: ctk.CTkScrollbar,
        h_scrollbar: ctk.CTkScrollbar,
        data_model: TableDataModel,
        layout_mgr: ColumnLayoutManager,
        *,
        get_row_height: Callable[[], int],
        commit_edit: Callable[[], None],
        redraw: Callable[[], None],
        on_viewport_resized: Callable[[], None],
    ) -> None:
        """Wire the controller to the table through shared collaborators and plain callbacks.

        Args:
            widget: The table widget, used only to read the DPI scaling factor.
            table_canvas: The body canvas whose size sets how far the table can scroll.
            header_canvas: The header canvas, which also reacts to the mouse wheel.
            v_scrollbar: The vertical scrollbar, which is connected to this controller.
            h_scrollbar: The horizontal scrollbar, which is connected to this controller.
            data_model: Source of the current row count.
            layout_mgr: Provides column geometry for the total content width.
            get_row_height: Returns the on-screen row height in pixels.
            commit_edit: Saves any open cell editor before the view moves.
            redraw: Repaints the table after the view moves.
            on_viewport_resized: Called after the body canvas is resized and the scroll position is clamped.
        """
        self._widget = widget
        self._table_canvas = table_canvas
        self._header_canvas = header_canvas
        self._v_scrollbar = v_scrollbar
        self._h_scrollbar = h_scrollbar
        self._data_model = data_model
        self._layout_mgr = layout_mgr
        self._get_row_height = get_row_height
        self._commit_edit = commit_edit
        self._redraw = redraw
        self._on_viewport_resized = on_viewport_resized

        self._scroll_x: float = 0.0
        self._scroll_y: float = 0.0

    @property
    def scroll_x(self) -> float:
        """Return how many pixels the table is scrolled to the right."""
        return self._scroll_x

    @property
    def scroll_y(self) -> float:
        """Return how many pixels the table is scrolled down."""
        return self._scroll_y

    def bind_events(self) -> None:
        """Connect the scrollbars, mouse wheel, and canvas resize events to this controller."""
        self._v_scrollbar.configure(command=self.on_v_scrollbar_command)
        self._h_scrollbar.configure(command=self.on_h_scrollbar_command)

        self._table_canvas.bind("<Configure>", self._on_canvas_configure)
        for canvas in (self._table_canvas, self._header_canvas):
            canvas.bind("<MouseWheel>", self._on_mousewheel_v)
            canvas.bind("<Shift-MouseWheel>", self._on_mousewheel_h)

    # -------------------------------------------------------------------------
    # Position Control
    # -------------------------------------------------------------------------

    def get_page_row_count(self) -> int:
        """Return how many whole rows fit in the visible body area, never less than one."""
        return max(1, self._table_canvas.winfo_height() // self._get_row_height())

    def reset_vertical(self) -> None:
        """Jump back to the top of the table without repainting."""
        self._scroll_y = 0.0

    def reset_horizontal(self) -> None:
        """Jump back to the left edge of the table without repainting."""
        self._scroll_x = 0.0

    def clamp_vertical(self) -> None:
        """Pull the view back up if it now points past the last row."""
        self._scroll_y = min(self._scroll_y, self._get_max_scroll_y())

    def clamp_to_bounds(self) -> None:
        """Pull the view back inside the table if it now points past the last row or column."""
        self.clamp_vertical()
        self._scroll_x = min(self._scroll_x, self._get_max_scroll_x())

    def scroll_to(self, row: int | None = None, col: int | None = None) -> None:
        """Scroll just far enough that the given row and column are fully visible, then repaint."""
        canvas_width = self._table_canvas.winfo_width()
        canvas_height = self._table_canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        if row is not None and self._data_model.row_count > 0:
            target_r = max(0, min(self._data_model.row_count - 1, row))
            row_height = self._get_row_height()
            target_y_top = target_r * row_height
            target_y_bottom = target_y_top + row_height

            if target_y_top < self._scroll_y:
                self._scroll_y = float(target_y_top)
            elif target_y_bottom > self._scroll_y + canvas_height:
                self._scroll_y = float(target_y_bottom - canvas_height)

        if col is not None:
            visible_cols = self._layout_mgr.get_visible_columns()
            if col in visible_cols:
                _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
                target_pos = visible_cols.index(col)
                target_x_left = col_offsets[target_pos]
                target_x_right = col_offsets[target_pos + 1]

                if target_x_left < self._scroll_x:
                    self._scroll_x = float(target_x_left)
                elif target_x_right > self._scroll_x + canvas_width:
                    self._scroll_x = float(target_x_right - canvas_width)

        self._redraw()

    # -------------------------------------------------------------------------
    # Scrollbar Commands
    # -------------------------------------------------------------------------

    def on_v_scrollbar_command(self, action: str, *args: Any) -> None:
        """Move the view when the vertical scrollbar is dragged or clicked."""
        if self._data_model.row_count == 0:
            return
        self._commit_edit()
        row_height = self._get_row_height()
        total_height = self._data_model.row_count * row_height

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_y = max(0.0, min(self._get_max_scroll_y(), fraction * total_height))
            self._redraw()
        elif action == "scroll" and len(args) >= 2:
            step_count = int(args[0])
            unit = args[1]
            page_height = self._table_canvas.winfo_height()
            self._scroll_y_by(step_count * (row_height * MOUSEWHEEL_STEP_ROWS if unit == "units" else page_height))

    def on_h_scrollbar_command(self, action: str, *args: Any) -> None:
        """Move the view when the horizontal scrollbar is dragged or clicked."""
        self._commit_edit()
        total_width = self._get_total_content_width()

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_x = max(0.0, min(self._get_max_scroll_x(), fraction * total_width))
            self._redraw()
        elif action == "scroll" and len(args) >= 2:
            step_count = int(args[0])
            unit = args[1]
            page_width = self._table_canvas.winfo_width()
            step_width = scale(self._widget, HORIZONTAL_SCROLL_STEP_PX) if unit == "units" else page_width
            self._scroll_x_by(step_count * step_width)

    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------

    def _on_canvas_configure(self, _event: Any) -> None:
        """Keep the view inside the table whenever the window size changes."""
        self.clamp_to_bounds()
        self._on_viewport_resized()

    def _on_mousewheel_v(self, event: Any) -> None:
        """Scroll up or down when the mouse wheel turns."""
        if self._data_model.row_count == 0:
            return
        delta = -int((event.delta / MOUSEWHEEL_BASE_DELTA) * self._get_row_height() * MOUSEWHEEL_STEP_ROWS)
        self._scroll_y_by(delta)

    def _on_mousewheel_h(self, event: Any) -> None:
        """Scroll left or right when the mouse wheel turns with Shift held."""
        delta = -int((event.delta / MOUSEWHEEL_BASE_DELTA) * scale(self._widget, HORIZONTAL_SCROLL_STEP_PX))
        self._scroll_x_by(delta)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _get_total_content_width(self) -> int:
        """Return the combined pixel width of all visible columns."""
        _, col_offsets = self._layout_mgr.calculate_geometry(self._table_canvas.winfo_width())
        return col_offsets[-1]

    def _get_max_scroll_y(self) -> float:
        """Calculate the furthest distance in pixels the table can scroll down."""
        total_height = self._data_model.row_count * self._get_row_height()
        return max(0.0, float(total_height - self._table_canvas.winfo_height()))

    def _get_max_scroll_x(self) -> float:
        """Calculate the furthest distance in pixels the table can scroll to the right."""
        return max(0.0, float(self._get_total_content_width() - self._table_canvas.winfo_width()))

    def _scroll_y_by(self, delta_pixels: float) -> None:
        """Shift the view up or down by a number of pixels, stopping at the table edges."""
        self._commit_edit()
        self._scroll_y = max(0.0, min(self._get_max_scroll_y(), self._scroll_y + delta_pixels))
        self._redraw()

    def _scroll_x_by(self, delta_pixels: float) -> None:
        """Shift the view left or right by a number of pixels, stopping at the table edges."""
        self._commit_edit()
        self._scroll_x = max(0.0, min(self._get_max_scroll_x(), self._scroll_x + delta_pixels))
        self._redraw()
