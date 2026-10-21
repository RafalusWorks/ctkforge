"""High-performance virtualized table widget for CustomTkinter.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

import tkinter as tk
import tkinter.font as tkfont
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Sequence
from contextlib import suppress
from typing import Any, Literal, overload, override

import customtkinter as ctk

from ctkforge.geometry import scale, unscale
from ctkforge.table.canvas_renderer import TableRenderer
from ctkforge.table.cell_editor import CellEditor
from ctkforge.table.column_resizer import ColumnResizer
from ctkforge.table.constants import (
    AUTOFIT_FALLBACK_WIDTH,
    AUTOFIT_PADDING_PX,
    AUTOFIT_SAMPLE_ROWS,
    CELL_HORIZONTAL_PADDING,
    DEFAULT_BORDER_SPACING,
    DEFAULT_HEADER_HEIGHT,
    DEFAULT_OVERSCAN_COLS,
    DEFAULT_OVERSCAN_ROWS,
    DEFAULT_ROW_HEIGHT,
    DIVIDER_HOVER_TOLERANCE,
    HORIZONTAL_SCROLL_STEP_PX,
    MIN_COLUMN_WIDTH,
    MIN_HEADER_HEIGHT,
    MIN_ROW_HEIGHT,
    MOUSEWHEEL_BASE_DELTA,
    MOUSEWHEEL_STEP_ROWS,
    TK_CONTROL_MASK,
    TK_SHIFT_MASK,
)
from ctkforge.table.data_model import TableDataModel
from ctkforge.table.selection_manager import SelectionManager

__all__ = ["CTkTable"]


class CTkTable(ctk.CTkFrame):
    """A fast, modern data table widget for CustomTkinter with sorting, selection, and cell editing."""

    def __init__(
        self,
        master: Any,
        # Widget Frame & Layout
        width: int = 600,
        height: int = 400,
        corner_radius: int | None = None,
        border_width: int | None = None,
        border_spacing: int = DEFAULT_BORDER_SPACING,
        fg_color: str | tuple[str, str] | None = None,
        border_color: str | tuple[str, str] | None = None,
        # Column Headers
        headers: list[str] | None = None,
        header_height: int = DEFAULT_HEADER_HEIGHT,
        header_fg_color: str | tuple[str, str] | None = None,
        header_text_color: str | tuple[str, str] | None = None,
        header_font: tuple[str, int] | ctk.CTkFont | None = None,
        header_sortable: bool = True,
        header_sortable_exclude: list[int] | None = None,
        # Dataset, Rows & Columns
        values: list[list[Any]] | None = None,
        column_widths: list[int] | dict[int, int] | None = None,
        column_types: list[str] | dict[int, str] | None = None,
        column_sort_keys: dict[int, Callable[[Any], Any]] | None = None,
        text_color: str | tuple[str, str] | None = None,
        font: tuple[str, int] | ctk.CTkFont | None = None,
        row_height: int = DEFAULT_ROW_HEIGHT,
        row_color: str | tuple[str, str] | None = None,
        alternate_row_color: str | tuple[str, str] | None = None,
        # Selection & Interaction
        selection_target: Literal["row", "cell"] = "row",
        selection_mode: Literal["single", "extended", "none"] = "single",
        selected_color: str | tuple[str, str] | None = None,
        selected_text_color: str | tuple[str, str] | None = None,
        command: Callable[[Any], None] | None = None,
        copyable: bool = False,
        # In-Place Cell Editing
        editable: bool = False,
        editable_columns_exclude: list[int] | None = None,
        on_cell_edit: Callable[[int, int, Any, Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        theme = ctk.ThemeManager.theme
        resolved_corner_radius = (
            theme["CTkFrame"]["corner_radius"]
            if corner_radius is None
            else corner_radius
        )
        resolved_border_width = (
            theme["CTkFrame"]["border_width"] if border_width is None else border_width
        )
        resolved_fg_color = (
            theme["CTkFrame"]["fg_color"] if fg_color is None else fg_color
        )
        resolved_border_color = (
            theme["CTkFrame"]["border_color"] if border_color is None else border_color
        )

        self._border_spacing: int = max(0, border_spacing)
        self._overscan_rows: int = DEFAULT_OVERSCAN_ROWS
        self._overscan_cols: int = DEFAULT_OVERSCAN_COLS

        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=resolved_corner_radius,
            border_width=resolved_border_width,
            fg_color=resolved_fg_color,
            border_color=resolved_border_color,
            **kwargs,
        )

        # Core Collaborator Engines
        self._data_model = TableDataModel(
            values=values,
            column_types=column_types,
            column_sort_keys=column_sort_keys,
        )
        self._selection_manager = SelectionManager(
            target=selection_target,
            mode=selection_mode,
        )
        self._renderer = TableRenderer()

        self._headers: list[str] | None = headers
        self._column_widths: list[int] | dict[int, int] | None = column_widths

        # Editing rules
        self._editable: bool = editable
        self._editable_columns_exclude: list[int] | None = editable_columns_exclude
        self.on_cell_edit: Callable[[int, int, Any, Any], None] | None = on_cell_edit

        # Header sorting rules
        self._header_sortable: bool = header_sortable
        self._header_sortable_exclude: list[int] | None = header_sortable_exclude

        self._row_height: int = max(MIN_ROW_HEIGHT, row_height)
        self._header_height: int = max(MIN_HEADER_HEIGHT, header_height)
        self.command: Callable[[Any], None] | None = command
        self._copyable: bool = copyable

        # Interactive column resize state
        self._column_resizer = ColumnResizer()

        # Typography & Color tokens
        self._font: tuple[str, int] | ctk.CTkFont = (
            ctk.CTkFont() if font is None else font
        )
        self._header_font: tuple[str, int] | ctk.CTkFont = (
            ctk.CTkFont(weight="bold") if header_font is None else header_font
        )
        self._text_color: str | tuple[str, str] = (
            theme["CTkLabel"]["text_color"] if text_color is None else text_color
        )
        self._header_text_color: str | tuple[str, str] = (
            theme["CTkLabel"]["text_color"]
            if header_text_color is None
            else header_text_color
        )
        self._selected_color: str | tuple[str, str] = (
            theme["CTkButton"]["fg_color"] if selected_color is None else selected_color
        )
        self._selected_text_color: str | tuple[str, str] = (
            theme["CTkButton"]["text_color"]
            if selected_text_color is None
            else selected_text_color
        )
        self._header_fg_color: str | tuple[str, str] | list[str] = (
            theme["CTkFrame"].get("top_fg_color", theme["CTkFrame"]["fg_color"])
            if header_fg_color is None
            else header_fg_color
        )
        self._row_color: str | tuple[str, str] | None = row_color
        self._alternate_row_color: str | tuple[str, str] | None = alternate_row_color
        self._divider_color: str | tuple[str, str] | list[str] = (
            border_color
            if border_color is not None
            else theme["CTkFrame"]["border_color"]
        )

        # Virtual scroll coordinates
        self._scroll_y: float = 0.0
        self._scroll_x: float = 0.0

        # Grid configuration
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Header and Body Viewport Canvases
        self._header_canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            height=scale(self, self._header_height),
        )
        self._header_corner = tk.Frame(self, highlightthickness=0, bd=0)
        self._table_canvas = tk.Canvas(self, highlightthickness=0, bd=0, takefocus=1)

        self._v_scrollbar = ctk.CTkScrollbar(
            self, orientation="vertical", command=self._on_v_scrollbar_command
        )
        self._h_scrollbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self._on_h_scrollbar_command
        )
        self._bottom_corner = tk.Frame(self, highlightthickness=0, bd=0)

        self._editor = CellEditor(
            canvas=self._table_canvas,
            on_commit=self._commit_edit,
            on_cancel=self._cancel_edit,
        )

        self._cached_colors: dict[str, str] = {}
        self._re_grid_components()
        self._setup_event_bindings()
        self._update_colors()

    # -------------------------------------------------------------------------
    # Event Bindings Setup
    # -------------------------------------------------------------------------

    def _setup_event_bindings(self) -> None:
        """Register mouse, keyboard, resize, and edit handlers across canvases."""
        self._table_canvas.bind("<Configure>", self._on_canvas_configure)
        self._table_canvas.bind("<MouseWheel>", self._on_mousewheel_v)
        self._table_canvas.bind("<Shift-MouseWheel>", self._on_mousewheel_h)

        self._header_canvas.bind("<MouseWheel>", self._on_mousewheel_v)
        self._header_canvas.bind("<Shift-MouseWheel>", self._on_mousewheel_h)

        self._table_canvas.bind("<Button-1>", self._on_body_click)
        self._table_canvas.bind("<Double-Button-1>", self._on_body_double_click)

        # Keyboard Navigation
        self._table_canvas.bind("<Up>", lambda e: self._navigate_focus(-1, 0, e))
        self._table_canvas.bind("<Down>", lambda e: self._navigate_focus(1, 0, e))
        self._table_canvas.bind("<Left>", lambda e: self._navigate_focus(0, -1, e))
        self._table_canvas.bind("<Right>", lambda e: self._navigate_focus(0, 1, e))
        self._table_canvas.bind("<Return>", self._on_enter_key)
        self._table_canvas.bind("<Prior>", self._on_page_up)
        self._table_canvas.bind("<Next>", self._on_page_down)
        self._table_canvas.bind("<Home>", self._on_home)
        self._table_canvas.bind("<End>", self._on_end)
        self._table_canvas.bind("<Control-a>", self._on_select_all)
        self._table_canvas.bind("<Control-c>", self._on_copy_shortcut)
        self._table_canvas.bind("<space>", self._on_space)
        self._table_canvas.bind("<Escape>", self._on_escape_key)

        # Header Column Resizing and Sorting
        self._header_canvas.bind("<Motion>", self._on_header_motion)
        self._header_canvas.bind("<Button-1>", self._on_header_click)
        self._header_canvas.bind("<B1-Motion>", self._on_header_drag)
        self._header_canvas.bind("<ButtonRelease-1>", self._on_header_release)
        self._header_canvas.bind("<Double-Button-1>", self._on_header_double_click)

    # -------------------------------------------------------------------------
    # Color & Layout Configuration
    # -------------------------------------------------------------------------

    def _resolve_color(self, color: str | tuple[str, str] | list[str] | None) -> str:
        """Resolve a CustomTkinter light/dark color tuple into a hex string for Tk canvas."""
        if color is None:
            return ""
        if isinstance(color, (tuple, list)):
            mode = ctk.get_appearance_mode()
            return color[1] if mode == "Dark" else color[0]
        return color

    def _update_colors(self) -> None:
        """Synchronize raw Tkinter canvas backgrounds and cache resolved theme colors."""
        canvas_bg = self._resolve_color(self._fg_color)
        if not canvas_bg or canvas_bg == "transparent":
            canvas_bg = self._resolve_color(
                ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
            )
        self._table_canvas.configure(bg=canvas_bg)
        self._header_canvas.configure(bg=canvas_bg)
        self._header_corner.configure(bg=canvas_bg)
        self._bottom_corner.configure(bg=canvas_bg)

        base_color = self._row_color if self._row_color is not None else self._fg_color
        alt_color = (
            self._alternate_row_color
            if self._alternate_row_color is not None
            else base_color
        )

        self._cached_colors = {
            "header_fg": self._resolve_color(self._header_fg_color),
            "header_text": self._resolve_color(self._header_text_color),
            "divider": self._resolve_color(self._divider_color),
            "text": self._resolve_color(self._text_color),
            "selected_bg": self._resolve_color(self._selected_color),
            "selected_text": self._resolve_color(self._selected_text_color),
            "row_even": self._resolve_color(base_color),
            "row_odd": self._resolve_color(alt_color),
        }

    @override
    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        self._update_colors()
        self._redraw()

    @override
    def _set_scaling(self, *args: Any, **kwargs: Any) -> None:
        super()._set_scaling(*args, **kwargs)
        self._re_grid_components()
        self._redraw()

    def _get_border_spacing(self) -> int:
        border = int(self._border_width) if self._border_width else 0
        raw_spacing = self._border_spacing + border
        return scale(self, raw_spacing)

    def _re_grid_components(self) -> None:
        spacing = self._get_border_spacing()

        if self._headers is not None:
            self._header_canvas.grid(
                row=0, column=0, sticky="nsew", padx=(spacing, 0), pady=(spacing, 0)
            )
            self._header_corner.grid(
                row=0, column=1, sticky="nsew", padx=(0, spacing), pady=(spacing, 0)
            )
            body_pady = (0, 0)
        else:
            self._header_canvas.grid_remove()
            self._header_corner.grid_remove()
            body_pady = (spacing, 0)

        self._table_canvas.grid(
            row=1, column=0, sticky="nsew", padx=(spacing, 0), pady=body_pady
        )
        self._v_scrollbar.grid(
            row=1, column=1, sticky="ns", padx=(0, spacing), pady=body_pady
        )
        self._h_scrollbar.grid(
            row=2, column=0, sticky="ew", padx=(spacing, 0), pady=(0, spacing)
        )
        self._bottom_corner.grid(
            row=2, column=1, sticky="nsew", padx=(0, spacing), pady=(0, spacing)
        )

    def _get_scaled_row_height(self) -> int:
        return scale(self, self._row_height)

    def _get_scaled_header_height(self) -> int:
        return scale(self, self._header_height)

    def _get_total_cols(self) -> int:
        if self._headers is not None:
            return len(self._headers)
        if self._data_model.row_count > 0 and self._data_model.values[0]:
            return len(self._data_model.values[0])
        return 0

    def _calculate_column_geometry(
        self, canvas_width: int
    ) -> tuple[list[int], list[int]]:
        """Compute pixel widths and cumulative prefix-sum offsets for all columns."""
        num_cols = self._get_total_cols()
        if num_cols == 0:
            return [], [0]

        min_col_w = scale(self, MIN_COLUMN_WIDTH)
        col_widths: list[int] = []

        if self._column_widths is not None:
            for c in range(num_cols):
                if (
                    isinstance(self._column_widths, list)
                    and c < len(self._column_widths)
                ) or (
                    isinstance(self._column_widths, dict) and c in self._column_widths
                ):
                    w = scale(self, self._column_widths[c])
                else:
                    w = min_col_w
                col_widths.append(max(min_col_w, w))
        else:
            uniform_w = max(
                min_col_w, canvas_width // num_cols if canvas_width > 0 else min_col_w
            )
            col_widths = [uniform_w] * num_cols

        # Stretch columns if they sum to less than canvas width
        total_explicit_w = sum(col_widths)
        if total_explicit_w < canvas_width and num_cols > 0:
            col_widths[-1] += canvas_width - total_explicit_w

        col_offsets = [0]
        cumulative = 0
        for w in col_widths:
            cumulative += w
            col_offsets.append(cumulative)

        return col_widths, col_offsets

    # -------------------------------------------------------------------------
    # Scrolling & Viewport Positioning
    # -------------------------------------------------------------------------

    def _get_max_scroll_y(self) -> float:
        """Calculate the furthest distance in pixels the table can scroll down."""
        total_height = self._data_model.row_count * self._get_scaled_row_height()
        canvas_height = self._table_canvas.winfo_height()
        return max(0.0, float(total_height - canvas_height))

    def _get_max_scroll_x(self, total_content_width: int) -> float:
        """Calculate the furthest distance in pixels the table can scroll to the right."""
        canvas_width = self._table_canvas.winfo_width()
        return max(0.0, float(total_content_width - canvas_width))

    def _scroll_y_by(self, delta_pixels: float) -> None:
        """Shift the vertical view up or down by a given number of pixels."""
        self._commit_edit()
        max_scroll_y = self._get_max_scroll_y()
        self._scroll_y = max(0.0, min(max_scroll_y, self._scroll_y + delta_pixels))
        self._redraw()

    def _scroll_x_by(self, delta_pixels: float) -> None:
        """Shift the horizontal view left or right by a given number of pixels."""
        self._commit_edit()
        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._calculate_column_geometry(canvas_width)
        max_scroll_x = self._get_max_scroll_x(col_offsets[-1])
        self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x + delta_pixels))
        self._redraw()

    def _on_mousewheel_v(self, event: Any) -> None:
        """Scroll the table up or down when the user turns the mouse wheel."""
        if self._data_model.row_count == 0:
            return
        scaled_row = self._get_scaled_row_height()
        delta = -int(
            (event.delta / MOUSEWHEEL_BASE_DELTA) * scaled_row * MOUSEWHEEL_STEP_ROWS
        )
        self._scroll_y_by(delta)

    def _on_mousewheel_h(self, event: Any) -> None:
        """Scroll the table left or right when the user turns the mouse wheel with Shift held."""
        delta = -int(
            (event.delta / MOUSEWHEEL_BASE_DELTA)
            * scale(self, HORIZONTAL_SCROLL_STEP_PX)
        )
        self._scroll_x_by(delta)

    def _on_v_scrollbar_command(self, action: str, *args: Any) -> None:
        """Handle clicks and drag actions from the vertical scrollbar."""
        if self._data_model.row_count == 0:
            return
        self._commit_edit()
        scaled_row = self._get_scaled_row_height()
        total_height = self._data_model.row_count * scaled_row
        canvas_height = self._table_canvas.winfo_height()
        max_scroll_y = self._get_max_scroll_y()

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_y = max(0.0, min(max_scroll_y, fraction * total_height))
            self._redraw()
        elif action == "scroll" and len(args) >= 2:
            step_count = int(args[0])
            unit = args[1]
            delta = step_count * (
                scaled_row * MOUSEWHEEL_STEP_ROWS if unit == "units" else canvas_height
            )
            self._scroll_y_by(delta)

    def _on_h_scrollbar_command(self, action: str, *args: Any) -> None:
        """Handle clicks and drag actions from the horizontal scrollbar."""
        self._commit_edit()
        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._calculate_column_geometry(canvas_width)
        total_width = col_offsets[-1]
        max_scroll_x = self._get_max_scroll_x(total_width)

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_x = max(0.0, min(max_scroll_x, fraction * total_width))
            self._redraw()
        elif action == "scroll" and len(args) >= 2:
            step_count = int(args[0])
            unit = args[1]
            delta = step_count * (
                scale(self, HORIZONTAL_SCROLL_STEP_PX)
                if unit == "units"
                else canvas_width
            )
            self._scroll_x_by(delta)

    def _on_canvas_configure(self, _event: Any) -> None:
        """Keep the view within safe bounds and resize the header whenever the window size changes."""
        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._calculate_column_geometry(canvas_width)
        self._scroll_y = min(self._scroll_y, self._get_max_scroll_y())
        self._scroll_x = min(self._scroll_x, self._get_max_scroll_x(col_offsets[-1]))
        self._header_canvas.configure(height=self._get_scaled_header_height())
        self._redraw()

    def scroll_to(self, row: int | None = None, col: int | None = None) -> None:
        """Scroll the view automatically so a specific row or column is visible on screen."""
        canvas_width = self._table_canvas.winfo_width()
        canvas_height = self._table_canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        if row is not None and self._data_model.row_count > 0:
            target_r = max(0, min(self._data_model.row_count - 1, row))
            scaled_row = self._get_scaled_row_height()
            target_y_top = target_r * scaled_row
            target_y_bottom = target_y_top + scaled_row

            if target_y_top < self._scroll_y:
                self._scroll_y = float(target_y_top)
            elif target_y_bottom > self._scroll_y + canvas_height:
                self._scroll_y = float(target_y_bottom - canvas_height)

        if col is not None:
            col_widths, col_offsets = self._calculate_column_geometry(canvas_width)
            total_cols = len(col_widths)
            if total_cols > 0:
                target_c = max(0, min(total_cols - 1, col))
                target_x_left = col_offsets[target_c]
                target_x_right = col_offsets[target_c + 1]

                if target_x_left < self._scroll_x:
                    self._scroll_x = float(target_x_left)
                elif target_x_right > self._scroll_x + canvas_width:
                    self._scroll_x = float(target_x_right - canvas_width)

        self._redraw()

    # -------------------------------------------------------------------------
    # In-Place Editing Lifecycle
    # -------------------------------------------------------------------------

    def _is_column_editable(self, col: int) -> bool:
        """Check whether users are allowed to edit cells in this column."""
        is_excluded = bool(
            self._editable_columns_exclude and col in self._editable_columns_exclude
        )
        return is_excluded if not self._editable else not is_excluded

    def _start_editing(self, visual_row: int, col: int) -> None:
        """Open a floating text box over the target cell so the user can type."""
        if not self._is_column_editable(col):
            return
        if not (
            0 <= visual_row < self._data_model.row_count
            and 0 <= col < self._get_total_cols()
        ):
            return

        self._commit_edit()
        self.scroll_to(row=visual_row, col=col)

        canvas_width = self._table_canvas.winfo_width()
        col_widths, col_offsets = self._calculate_column_geometry(canvas_width)
        scaled_row = self._get_scaled_row_height()

        x_left = col_offsets[col] - self._scroll_x
        col_w = col_widths[col]
        y_top = visual_row * scaled_row - self._scroll_y

        try:
            current_val = str(self._data_model.get_cell(visual_row, col))
        except IndexError:
            current_val = ""

        border_color_hex = self._cached_colors.get(
            "selected_bg", self._resolve_color(self._selected_color)
        )

        self._editor.start_editing(
            display_row=visual_row,
            col_index=col,
            initial_value=current_val,
            x_left=x_left,
            y_top=y_top,
            width=col_w,
            height=scaled_row,
            font=self._font,
            border_color=border_color_hex,
        )

    def _commit_edit(self) -> None:
        """Save edited text, bake sort if editing active sort column, and destroy editor."""
        if not self._editor.is_editing:
            return

        active_cell = self._editor.editing_cell
        if active_cell is None:
            return

        visual_r, c = active_cell
        new_val = self._editor.get_text()

        try:
            old_val = self._data_model.get_cell(visual_r, c)
        except IndexError:
            old_val = ""

        if new_val != str(old_val):
            old_val, storage_row = self._data_model.update_cell(visual_r, c, new_val)

            # Option 1: Bake current visual order if editing the active sort column
            if self._data_model.sort_column == c:
                self._data_model.commit_sort()
                storage_row = visual_r

            if self.on_cell_edit is not None:
                self.on_cell_edit(storage_row, c, old_val, new_val)

        self._editor.destroy_editor()
        with suppress(tk.TclError):
            self._table_canvas.focus_set()
        self._redraw()

    def _cancel_edit(self) -> None:
        """Close the open text box and discard any unsaved changes."""
        self._editor.destroy_editor()
        with suppress(tk.TclError):
            self._table_canvas.focus_set()
        self._redraw()

    # -------------------------------------------------------------------------
    # Mouse & Keyboard Event Handlers
    # -------------------------------------------------------------------------

    def _get_cell_at(self, pixel_x: float, pixel_y: float) -> tuple[int, int] | None:
        """Translate raw canvas pixel coordinates into (display_row, col_index), or None if out of bounds."""
        if self._data_model.row_count == 0:
            return None

        canvas_width = self._table_canvas.winfo_width()
        col_widths, col_offsets = self._calculate_column_geometry(canvas_width)
        scaled_row = self._get_scaled_row_height()

        row = int((pixel_y + self._scroll_y) // scaled_row)
        col = bisect_right(col_offsets, pixel_x + self._scroll_x) - 1

        if 0 <= row < self._data_model.row_count and 0 <= col < len(col_widths):
            return (row, col)
        return None

    def _on_body_click(self, event: Any) -> None:
        """Select the clicked row or cell and move keyboard focus to it."""
        self._commit_edit()
        with suppress(tk.TclError):
            self._table_canvas.focus_set()

        if self._selection_manager.mode == "none":
            return

        cell = self._get_cell_at(event.x, event.y)
        if cell is None:
            return

        clicked_r, clicked_c = cell
        is_ctrl = bool(event.state & TK_CONTROL_MASK)
        is_shift = bool(event.state & TK_SHIFT_MASK)

        self._selection_manager.apply_click(
            clicked_r, clicked_c, is_ctrl=is_ctrl, is_shift=is_shift
        )
        self._notify_command()
        self._redraw()

    def _on_body_double_click(self, event: Any) -> None:
        """Open the cell editor when the user double-clicks a cell."""
        self._commit_edit()
        if not self._editable and not self._editable_columns_exclude:
            return

        cell = self._get_cell_at(event.x, event.y)
        if cell is not None:
            self._start_editing(cell[0], cell[1])

    def _on_enter_key(self, _event: Any) -> str:
        """Start editing the currently focused cell when Enter is pressed."""
        focused_r = self._selection_manager.focused_row
        focused_c = self._selection_manager.focused_col
        if (
            focused_r is not None
            and focused_c is not None
            and self._is_column_editable(focused_c)
        ):
            self._start_editing(focused_r, focused_c)
        return "break"

    def _navigate_focus(self, delta_row: int, delta_col: int, event: Any) -> str:
        """Move keyboard focus by row and column offsets and slide the view if needed."""
        if self._data_model.row_count == 0:
            return "break"

        is_shift = bool(event.state & TK_SHIFT_MASK)
        total_cols = self._get_total_cols()

        new_r, new_c = self._selection_manager.navigate(
            delta_row=delta_row,
            delta_col=delta_col,
            total_rows=self._data_model.row_count,
            total_cols=total_cols,
            is_shift=is_shift,
        )

        scroll_c = new_c if self._selection_manager.target == "cell" else None
        self.scroll_to(row=new_r, col=scroll_c)
        self._notify_command()
        self._redraw()
        return "break"

    def _on_page_up(self, event: Any) -> str:
        """Jump focus up by one full screen page of rows."""
        canvas_h = self._table_canvas.winfo_height()
        scaled_r = self._get_scaled_row_height()
        page_rows = max(1, canvas_h // scaled_r)
        return self._navigate_focus(-page_rows, 0, event)

    def _on_page_down(self, event: Any) -> str:
        """Jump focus down by one full screen page of rows."""
        canvas_h = self._table_canvas.winfo_height()
        scaled_r = self._get_scaled_row_height()
        page_rows = max(1, canvas_h // scaled_r)
        return self._navigate_focus(page_rows, 0, event)

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
        self.select_all()
        return "break"

    def _on_space(self, _event: Any) -> str:
        """Toggle selection on the focused item when the Space bar is pressed."""
        focused_r = self._selection_manager.focused_row
        if focused_r is not None and self._selection_manager.mode in (
            "single",
            "extended",
        ):
            focused_c = self._selection_manager.focused_col or 0
            self._selection_manager.apply_click(
                focused_r, focused_c, is_ctrl=True, is_shift=False
            )
            self._notify_command()
            self._redraw()
        return "break"

    def _on_escape_key(self, _event: tk.Event) -> None:
        """Cancel any active cell edit or clear the current selection when Escape is pressed."""
        if self._editor.is_editing:
            self._cancel_edit()
        else:
            self.clear_selection()

    def _on_copy_shortcut(self, _event: Any = None) -> None:
        """Copy selected items to the clipboard when Ctrl+C is pressed."""
        if self._copyable:
            self.copy_selection()

    def _notify_command(self) -> None:
        """Fire the user-provided selection callback with current selected items."""
        if self.command:
            selected = (
                self.get_selected_rows()
                if self._selection_manager.target == "row"
                else self.get_selected_cells()
            )
            self.command(selected)

    # -------------------------------------------------------------------------
    # Column Header Mouse Handlers & Resizing
    # -------------------------------------------------------------------------

    def _is_column_header_sortable(self, col: int) -> bool:
        """Check whether clicking this column header is allowed to sort the table."""
        if not self._header_sortable:
            return False
        return not bool(
            self._header_sortable_exclude and col in self._header_sortable_exclude
        )

    def _toggle_header_sort(self, col: int) -> None:
        """Cycle column sorting between ascending, descending, and unsorted order."""
        current_sort_col, current_asc = (
            self._data_model.sort_column,
            self._data_model.sort_ascending,
        )
        if current_sort_col == col:
            if current_asc:
                self.sort_by(col, ascending=False)
            else:
                self.clear_sort()
        else:
            self.sort_by(col, ascending=True)

    def _on_header_motion(self, event: Any) -> None:
        """Change the mouse cursor to a resize arrow when hovering over divider lines."""
        if self._headers is None:
            return

        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._calculate_column_geometry(canvas_width)
        logical_x = event.x + self._scroll_x
        divider_tol = scale(self, DIVIDER_HOVER_TOLERANCE)

        matched = self._column_resizer.check_divider_hover(
            logical_x, col_offsets, divider_tol
        )
        if matched is not None:
            self._header_canvas.configure(cursor="sb_h_double_arrow")
        elif not self._column_resizer.is_resizing:
            self._header_canvas.configure(cursor="")

    def _on_header_click(self, event: Any) -> None:
        """Start dragging a column divider or sort the column that was clicked."""
        if self._column_resizer.hover_divider_col is not None:
            canvas_width = self._table_canvas.winfo_width()
            col_widths, _ = self._calculate_column_geometry(canvas_width)
            divider = self._column_resizer.hover_divider_col
            self._column_resizer.start_resize(divider, event.x, col_widths[divider - 1])
        else:
            canvas_width = self._table_canvas.winfo_width()
            col_widths, col_offsets = self._calculate_column_geometry(canvas_width)
            clicked_c = bisect_right(col_offsets, event.x + self._scroll_x) - 1
            if 0 <= clicked_c < len(col_widths) and self._is_column_header_sortable(
                clicked_c
            ):
                self._toggle_header_sort(clicked_c)

    def _on_header_drag(self, event: Any) -> None:
        """Resize the active column width as the user drags the mouse divider."""
        if self._column_resizer.is_resizing:
            min_col_w = scale(self, MIN_COLUMN_WIDTH)
            new_w = self._column_resizer.calculate_drag_width(event.x, min_col_w)

            canvas_width = self._table_canvas.winfo_width()
            col_widths, _ = self._calculate_column_geometry(canvas_width)
            unscaled_widths = [unscale(self, w) for w in col_widths]
            resizing_col = self._column_resizer.resizing_col
            if resizing_col is not None:
                unscaled_widths[resizing_col] = unscale(self, new_w)
                self._column_widths = unscaled_widths
                self._redraw()

    def _on_header_release(self, _event: Any) -> None:
        """Stop column resizing and restore the standard mouse cursor."""
        self._column_resizer.end_resize()
        self._header_canvas.configure(cursor="")

    def _on_header_double_click(self, _event: Any) -> None:
        """Automatically fit column width to content when a divider line is double-clicked."""
        if self._column_resizer.hover_divider_col is not None:
            self.auto_fit_column(self._column_resizer.hover_divider_col - 1)

    def auto_fit_columns(self, columns: list[int] | None = None) -> None:
        """Calculate and snap column widths to fit content in a single batched pass."""
        total_cols = self._get_total_cols()
        if total_cols == 0:
            return

        target_cols = (
            [c for c in columns if 0 <= c < total_cols]
            if columns is not None
            else list(range(total_cols))
        )
        if not target_cols:
            return

        scaled_hfont = self._apply_font_scaling(self._header_font)
        header_font_obj = tkfont.Font(font=scaled_hfont)
        scaled_bfont = self._apply_font_scaling(self._font)
        body_font_obj = tkfont.Font(font=scaled_bfont)

        padding = scale(self, AUTOFIT_PADDING_PX)
        sample_rows = min(AUTOFIT_SAMPLE_ROWS, self._data_model.row_count)

        if isinstance(self._column_widths, list):
            while len(self._column_widths) < total_cols:
                self._column_widths.append(unscale(self, MIN_COLUMN_WIDTH))
        elif not isinstance(self._column_widths, dict):
            self._column_widths = {}

        for col_index in target_cols:
            header_text = (
                self._headers[col_index]
                if (self._headers and col_index < len(self._headers))
                else None
            )
            sample_values: list[str] = []
            for r in range(sample_rows):
                try:
                    sample_values.append(str(self._data_model.get_cell(r, col_index)))
                except IndexError:
                    pass

            fitted_w = ColumnResizer.calculate_autofit_width(
                header_text=header_text,
                sample_values=sample_values,
                header_measure=header_font_obj.measure,
                body_measure=body_font_obj.measure,
                padding=padding,
                fallback_width=AUTOFIT_FALLBACK_WIDTH,
            )
            fit_width = unscale(self, fitted_w)

            if isinstance(self._column_widths, (dict, list)):
                self._column_widths[col_index] = fit_width

        self._redraw()

    def auto_fit_column(self, col_index: int) -> None:
        """Calculate and snap column width to fit header and cell text without locking other columns."""
        self.auto_fit_columns([col_index])

    # -------------------------------------------------------------------------
    # Viewport Redraw Orchestrator
    # -------------------------------------------------------------------------

    def _redraw(self) -> None:
        """Synchronize header, body viewport, and scrollbars."""
        canvas_w = self._table_canvas.winfo_width()
        canvas_h = self._table_canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        col_widths, col_offsets = self._calculate_column_geometry(canvas_w)
        total_cols = len(col_widths)
        total_rows = self._data_model.row_count
        total_content_width = col_offsets[-1]

        if total_cols > 0:
            start_col = max(
                0, bisect_right(col_offsets, self._scroll_x) - 1 - self._overscan_cols
            )
            end_col = min(
                total_cols,
                bisect_left(col_offsets, self._scroll_x + canvas_w)
                + 1
                + self._overscan_cols,
            )
        else:
            start_col, end_col = 0, 0

        scaled_padding = scale(self, CELL_HORIZONTAL_PADDING)
        divider_hex = self._cached_colors.get(
            "divider", self._resolve_color(self._divider_color)
        )

        # 1. Pinned Header Rendering
        if self._headers is not None:
            header_h = self._get_scaled_header_height()
            radius_val = int(self._corner_radius) if self._corner_radius else 0
            scaled_radius = scale(self, radius_val)

            self._renderer.render_header(
                canvas=self._header_canvas,
                headers=self._headers,
                col_widths=col_widths,
                col_offsets=col_offsets,
                start_col=start_col,
                end_col=end_col,
                scroll_x=self._scroll_x,
                header_height=header_h,
                canvas_width=canvas_w,
                corner_radius=scaled_radius,
                bg_hex=self._cached_colors.get(
                    "header_fg", self._resolve_color(self._header_fg_color)
                ),
                text_color_hex=self._cached_colors.get(
                    "header_text", self._resolve_color(self._header_text_color)
                ),
                divider_color_hex=divider_hex,
                header_font=self._apply_font_scaling(self._header_font),
                sort_col=self._data_model.sort_column,
                sort_ascending=self._data_model.sort_ascending,
                scaled_padding=scaled_padding,
            )

        # 2. Body Viewport Rendering
        scaled_row = self._get_scaled_row_height()
        total_content_height = total_rows * scaled_row

        start_row = max(0, int(self._scroll_y // scaled_row) - self._overscan_rows)
        end_row = min(
            total_rows,
            int((self._scroll_y + canvas_h) // scaled_row) + self._overscan_rows + 1,
        )

        self._renderer.render_body(
            canvas=self._table_canvas,
            data_model=self._data_model,
            selection_manager=self._selection_manager,
            col_widths=col_widths,
            col_offsets=col_offsets,
            start_col=start_col,
            end_col=end_col,
            start_row=start_row,
            end_row=end_row,
            scroll_x=self._scroll_x,
            scroll_y=self._scroll_y,
            scaled_row_height=scaled_row,
            canvas_width=canvas_w,
            text_color_hex=self._cached_colors.get(
                "text", self._resolve_color(self._text_color)
            ),
            selected_bg_hex=self._cached_colors.get(
                "selected_bg", self._resolve_color(self._selected_color)
            ),
            selected_text_hex=self._cached_colors.get(
                "selected_text", self._resolve_color(self._selected_text_color)
            ),
            row_even_bg=self._cached_colors.get("row_even", ""),
            row_odd_bg=self._cached_colors.get("row_odd", ""),
            divider_color_hex=divider_hex,
            body_font=self._apply_font_scaling(self._font),
            scaled_padding=scaled_padding,
        )

        # 3. Synchronize Scrollbars
        self._renderer.sync_scrollbars(
            v_scrollbar=self._v_scrollbar,
            h_scrollbar=self._h_scrollbar,
            scroll_x=self._scroll_x,
            scroll_y=self._scroll_y,
            total_content_width=total_content_width,
            total_content_height=total_content_height,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
        )

    # -------------------------------------------------------------------------
    # Public Selection API
    # -------------------------------------------------------------------------

    def get_selected_rows(self) -> list[int]:
        """Return sorted list of selected display row indexes."""
        return sorted(self._selection_manager.selected_rows)

    def get_selected_cells(self) -> list[tuple[int, int]]:
        """Return sorted list of selected (row, column) cell coordinates."""
        return sorted(self._selection_manager.selected_cells)

    def select_row(self, row_index: int, notify: bool = True) -> None:
        """Select a single row by display index."""
        self._selection_manager.select_row(row_index, self._data_model.row_count)
        if notify:
            self._notify_command()
        self._redraw()

    def deselect_row(self, row_index: int, notify: bool = True) -> None:
        """Deselect a row by display index."""
        self._selection_manager.deselect_row(row_index)
        if notify:
            self._notify_command()
        self._redraw()

    def select_cell(self, row_index: int, col_index: int, notify: bool = True) -> None:
        """Select a single cell by display coordinates."""
        total_cols = self._get_total_cols()
        self._selection_manager.select_cell(
            row_index, col_index, self._data_model.row_count, total_cols
        )
        if notify:
            self._notify_command()
        self._redraw()

    def select_all(self, notify: bool = True) -> None:
        """Select all visible rows or cells if extended mode is active."""
        total_cols = self._get_total_cols()
        self._selection_manager.select_all(self._data_model.row_count, total_cols)
        if notify:
            self._notify_command()
        self._redraw()

    def clear_selection(self, notify: bool = True) -> None:
        """Clear all active selections and focus rings."""
        self._selection_manager.clear()
        if notify:
            self._notify_command()
        self._redraw()

    def edit_focused_cell(self) -> None:
        """Trigger in-place editing on the currently focused cell."""
        f_row = self._selection_manager.focused_row
        f_col = self._selection_manager.focused_col
        if f_row is not None and f_col is not None:
            self._start_editing(f_row, f_col)

    def start_editing(self, row: int, col: int) -> None:
        """Public hook to initiate in-place editing at a given cell."""
        self._start_editing(row, col)

    # -------------------------------------------------------------------------
    # Public Clipboard & Data Manipulation API
    # -------------------------------------------------------------------------

    def copy_selection(self) -> str:
        """Copy selected rows or cells to the system clipboard as TSV."""
        tsv_data = self._selection_manager.export_tsv(self._data_model)
        if tsv_data:
            with suppress(tk.TclError):
                root = self.winfo_toplevel()
                root.clipboard_clear()
                root.clipboard_append(tsv_data)
        return tsv_data

    def get(self, row: int | None = None, column: int | None = None) -> Any:
        """Return table data in current visual display order."""
        if row is not None:
            if column is not None:
                return self.get_cell(row, column)
            return self.get_row(row)

        if column is not None:
            total_cols = self._get_total_cols()
            if not (0 <= column < total_cols):
                raise IndexError(
                    f"Column index {column} out of range [0, {total_cols})"
                )
            return [
                self._data_model.get_cell(r, column)
                for r in range(self._data_model.row_count)
            ]

        return self._data_model.get_all_rows()

    def get_row(self, row_index: int) -> list[Any]:
        """Return the record values at display index row_index."""
        return self._data_model.get_row(row_index)

    @overload
    def get_raw_row_index(self, display_row: int) -> int: ...

    @overload
    def get_raw_row_index(self, display_row: Sequence[int]) -> list[int]: ...

    def get_raw_row_index(self, display_row: int | Sequence[int]) -> int | list[int]:
        """Translate one or multiple visual display row indexes to raw storage indexes."""
        if isinstance(display_row, (list, tuple, set)):
            return [self._data_model.get_raw_row_index(r) for r in display_row]
        return self._data_model.get_raw_row_index(display_row)

    @overload
    def get_display_row_index(self, raw_row: int) -> int: ...

    @overload
    def get_display_row_index(self, raw_row: Sequence[int]) -> list[int]: ...

    def get_display_row_index(self, raw_row: int | Sequence[int]) -> int | list[int]:
        """Translate one or multiple raw row indexes to current visual display indexes."""
        if isinstance(raw_row, (list, tuple, set)):
            return [self._data_model.get_display_row_index(r) for r in raw_row]
        return self._data_model.get_display_row_index(raw_row)

    def get_cell(self, row_index: int, col_index: int) -> Any:
        """Return the cell value at display row and column."""
        return self._data_model.get_cell(row_index, col_index)

    def update_cell(
        self, row_index: int, col_index: int, value: Any, notify: bool = True
    ) -> None:
        """Update a specific cell value in-place, updating sorting if relevant."""
        old_val, storage_row = self._data_model.update_cell(row_index, col_index, value)

        if self._data_model.sort_column == col_index:
            self.sort_by(col_index, ascending=self._data_model.sort_ascending)
        else:
            self._redraw()

        if notify and self.on_cell_edit is not None:
            self.on_cell_edit(storage_row, col_index, old_val, value)

    def update_row(
        self, display_row: int, values: list[Any], notify: bool = True
    ) -> None:
        """Update an entire row in-place, updating sorting if relevant."""
        if (
            self._editor.is_editing
            and self._selection_manager.focused_row == display_row
        ):
            self._cancel_edit()

        total_cols = self._get_total_cols()
        old_row, storage_row = self._data_model.update_row(
            display_row, values, total_cols=total_cols
        )

        sort_col = self._data_model.sort_column
        if sort_col is not None and (
            sort_col >= len(old_row)
            or sort_col >= len(values)
            or old_row[sort_col] != values[sort_col]
        ):
            self.sort_by(sort_col, ascending=self._data_model.sort_ascending)
        else:
            self._redraw()

        if notify and self.on_cell_edit is not None:
            max_check = min(len(old_row), len(values))
            for c in range(max_check):
                if old_row[c] != values[c]:
                    self.on_cell_edit(storage_row, c, old_row[c], values[c])

    def insert_row(
        self, index: int | None = None, values: list[Any] | None = None
    ) -> int:
        """Insert a row at display position index (or append if None). Return the new display index."""
        self._cancel_edit()
        total_cols = self._get_total_cols()
        visual_insert_pos, _ = self._data_model.insert_row(index, values, total_cols)

        self._selection_manager.adjust_indexes_after_insert(visual_insert_pos)

        if self._data_model.sort_column is not None:
            self.sort_by(
                self._data_model.sort_column, ascending=self._data_model.sort_ascending
            )
            # Re-locate the newly inserted row's visual slot after re-sorting
            storage_insert_pos = self._data_model.row_count - 1
            visual_insert_pos = self._data_model.get_display_row_index(
                storage_insert_pos
            )
        else:
            self._redraw()

        return visual_insert_pos

    def delete_rows(self, row_indexes: list[int] | set[int] | int) -> None:
        """Delete one or multiple display rows and adjust selection mappings."""
        self._cancel_edit()
        deleted_targets = self._data_model.delete_rows(row_indexes)
        if not deleted_targets:
            return

        self._selection_manager.adjust_indexes_after_delete(
            deleted_targets, self._data_model.row_count
        )

        max_y = self._get_max_scroll_y()
        if self._scroll_y > max_y:
            self._scroll_y = max(0.0, max_y)

        self._redraw()
        self._notify_command()

    # -------------------------------------------------------------------------
    # Public Sorting API
    # -------------------------------------------------------------------------

    def sort_by(self, column_index: int, ascending: bool = True) -> None:
        """Sort rows via index indirection without mutating raw dataset storage."""
        self._commit_edit()
        total_cols = self._get_total_cols()
        if not (0 <= column_index < total_cols) or self._data_model.row_count == 0:
            return

        self._data_model.sort_by(column_index, ascending=ascending)
        self._redraw()

    def clear_sort(self) -> None:
        """Restore original unsorted order instantly."""
        self._commit_edit()
        self._data_model.clear_sort()
        self._redraw()

    def commit_sort(self) -> None:
        """Permanently bake current visual sorted order into the raw dataset and reset sort state."""
        self._commit_edit()
        self._data_model.commit_sort()
        self._redraw()

    def get_sort_state(self) -> tuple[int | None, bool]:
        """Return (sorted_column_index, is_ascending)."""
        return self._data_model.sort_column, self._data_model.sort_ascending

    # -------------------------------------------------------------------------
    # Public Read-Only Properties (Inspection)
    # -------------------------------------------------------------------------

    @property
    def is_editing(self) -> bool:
        """Return whether an in-place cell editor is currently active."""
        return self._editor.is_editing

    @override
    def cget(self, attribute_name: str) -> Any:
        """Retrieve table widget configuration options."""
        match attribute_name:
            case "values":
                return self._data_model.values
            case "headers":
                return self._headers
            case "column_widths":
                return self._column_widths
            case "column_types":
                return self._data_model.column_types
            case "column_sort_keys":
                return self._data_model.column_sort_keys
            case "header_sortable":
                return self._header_sortable
            case "header_sortable_exclude":
                return self._header_sortable_exclude
            case "editable":
                return self._editable
            case "editable_columns_exclude":
                return self._editable_columns_exclude
            case "selection_target":
                return self._selection_manager.target
            case "selection_mode":
                return self._selection_manager.mode
            case "copyable":
                return self._copyable
            case "row_height":
                return self._row_height
            case "header_height":
                return self._header_height
            case "row_color":
                return self._row_color
            case "alternate_row_color":
                return self._alternate_row_color
            case "selected_color":
                return self._selected_color
            case "selected_text_color":
                return self._selected_text_color
            case "border_spacing":
                return self._border_spacing
            case "command":
                return self.command
            case _:
                return super().cget(attribute_name)

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Configure widget options dynamically and refresh the viewport in a single batched pass."""
        needs_redraw = require_redraw
        re_grid = False

        if "values" in kwargs:
            new_values = kwargs.pop("values")
            self._commit_edit()
            self._data_model.reset_values(new_values)
            self._selection_manager.clear()
            self._scroll_y = 0.0
            needs_redraw = True

        if "headers" in kwargs:
            self._headers = kwargs.pop("headers")
            re_grid = True
            needs_redraw = True

        if "column_widths" in kwargs:
            self._column_widths = kwargs.pop("column_widths")
            self._scroll_x = 0.0
            needs_redraw = True

        if "editable" in kwargs:
            self._editable = bool(kwargs.pop("editable"))
            if not self._editable and self._editable_columns_exclude is None:
                self._cancel_edit()

        if "editable_columns_exclude" in kwargs:
            self._editable_columns_exclude = kwargs.pop("editable_columns_exclude")

        if "header_sortable" in kwargs:
            self._header_sortable = bool(kwargs.pop("header_sortable"))

        if "header_sortable_exclude" in kwargs:
            self._header_sortable_exclude = kwargs.pop("header_sortable_exclude")

        if "selection_target" in kwargs:
            self._selection_manager.set_target(kwargs.pop("selection_target"))
            needs_redraw = True

        if "selection_mode" in kwargs:
            self._selection_manager.set_mode(kwargs.pop("selection_mode"))
            needs_redraw = True

        if "copyable" in kwargs:
            self._copyable = bool(kwargs.pop("copyable"))

        if "row_height" in kwargs:
            self._row_height = max(MIN_ROW_HEIGHT, int(kwargs.pop("row_height")))
            needs_redraw = True

        if "header_height" in kwargs:
            self._header_height = max(
                MIN_HEADER_HEIGHT, int(kwargs.pop("header_height"))
            )
            needs_redraw = True

        if "border_spacing" in kwargs:
            self._border_spacing = max(0, int(kwargs.pop("border_spacing")))
            re_grid = True
            needs_redraw = True

        if "column_types" in kwargs:
            self._data_model.column_types = kwargs.pop("column_types")
            needs_redraw = True

        if "column_sort_keys" in kwargs:
            self._data_model.column_sort_keys = kwargs.pop("column_sort_keys")
            needs_redraw = True

        if "on_cell_edit" in kwargs:
            self.on_cell_edit = kwargs.pop("on_cell_edit")

        if "command" in kwargs:
            self.command = kwargs.pop("command")

        colors_changed = False
        for color_prop in (
            "selected_color",
            "selected_text_color",
            "row_color",
            "alternate_row_color",
            "text_color",
            "header_text_color",
        ):
            if color_prop in kwargs:
                setattr(self, f"_{color_prop}", kwargs.pop(color_prop))
                colors_changed = True
                needs_redraw = True

        if "header_fg_color" in kwargs:
            h_fg = kwargs.pop("header_fg_color")
            self._header_fg_color = (
                ctk.ThemeManager.theme["CTkFrame"].get(
                    "top_fg_color", ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
                )
                if h_fg is None
                else h_fg
            )
            colors_changed = True
            needs_redraw = True

        if colors_changed:
            self._update_colors()

        if "font" in kwargs:
            f_val = kwargs.pop("font")
            self._font = ctk.CTkFont() if f_val is None else f_val
            needs_redraw = True

        if "header_font" in kwargs:
            hf_val = kwargs.pop("header_font")
            self._header_font = ctk.CTkFont(weight="bold") if hf_val is None else hf_val
            needs_redraw = True

        if kwargs:
            if "corner_radius" in kwargs or "border_width" in kwargs:
                re_grid = True
            super().configure(**kwargs)
            self._update_colors()
            needs_redraw = True

        if re_grid:
            self._re_grid_components()

        if needs_redraw:
            self._redraw()

    @override
    def bind(
        self,
        sequence: str | None = None,
        command: Callable[[Any], Any] | None = None,
        add: Literal["", "+"] | bool | None = True,
    ) -> None:
        """Bind an event to both the container frame and the internal viewport canvas."""
        super().bind(sequence, command, add=add)
        if sequence and hasattr(self, "_table_canvas"):
            self._table_canvas.bind(sequence, command, add=add)
