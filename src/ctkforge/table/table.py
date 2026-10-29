"""High-performance virtualized table widget for CustomTkinter.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

import tkinter as tk
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Sequence
from contextlib import suppress
from typing import Any, Final, Literal, overload, override

import customtkinter as ctk

from ctkforge.geometry import scale
from ctkforge.table.canvas_renderer import TableRenderer
from ctkforge.table.cell_editor import CellEditor
from ctkforge.table.column_layout import ColumnLayoutManager
from ctkforge.table.constants import (
    CELL_HORIZONTAL_PADDING,
    DEFAULT_BORDER_SPACING,
    DEFAULT_HEADER_HEIGHT,
    DEFAULT_OVERSCAN_COLS,
    DEFAULT_OVERSCAN_ROWS,
    DEFAULT_ROW_HEIGHT,
    MIN_HEADER_HEIGHT,
    MIN_ROW_HEIGHT,
    TK_CONTROL_MASK,
    TK_SHIFT_MASK,
)
from ctkforge.table.data_model import TableDataModel
from ctkforge.table.header_controller import HeaderController
from ctkforge.table.keyboard_router import KeyboardRouter
from ctkforge.table.scroll_controller import ScrollController
from ctkforge.table.selection_manager import SelectionManager
from ctkforge.table.style_resolver import STYLE_OPTIONS, StyleResolver

__all__ = ["CTkTable"]

_REDRAW_OPTIONS: Final[frozenset[str]] = frozenset(
    {
        "values",
        "headers",
        "show_headers",
        "show_columns",
        "column_widths",
        "selection_target",
        "selection_mode",
        "row_height",
        "header_height",
        "border_spacing",
        "sort_key",
        "formatters",
    }
)

_REGRID_OPTIONS: Final[frozenset[str]] = frozenset(
    {
        "headers",
        "show_headers",
        "border_spacing",
    }
)


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
        headers: list[str] | dict[int | str, str] | None = None,
        show_headers: bool | None = None,
        header_height: int = DEFAULT_HEADER_HEIGHT,
        header_fg_color: str | tuple[str, str] | None = None,
        header_text_color: str | tuple[str, str] | dict[int | str, str | tuple[str, str]] | None = None,
        header_font: tuple[str, int] | ctk.CTkFont | str | dict[int | str, Any] | None = None,
        header_sortable: bool | dict[int | str, bool] = True,
        header_hover_color: str | tuple[str, str] | None = None,
        header_alignment: Literal["left", "center", "right"]
        | dict[int | str, Literal["left", "center", "right"]] = "left",
        # Dataset, Rows & Columns
        values: list[list[Any]] | None = None,
        show_columns: bool | dict[int | str, bool] = True,
        column_widths: int | Literal["auto"] | dict[int | str, int | Literal["auto"]] | None = None,
        sort_key: Literal["str", "int", "float", "date"]
        | Callable[[Any], Any]
        | dict[int | str, Literal["str", "int", "float", "date"] | Callable[[Any], Any]]
        | None = None,
        justify: Literal["left", "center", "right"] | dict[int | str, Literal["left", "center", "right"]] | None = None,
        text_color: str | tuple[str, str] | dict[int | str, str | tuple[str, str]] | None = None,
        font: tuple[str, int] | ctk.CTkFont | str | dict[int | str, Any] | None = None,
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
        editable: bool | dict[int | str, bool] = False,
        on_cell_edit: Callable[[int, int, Any, Any], None] | None = None,
        # Cell Presentation & Formatting
        formatters: Callable[[Any], Any] | dict[int | str, Callable[[Any], Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a virtualized data table widget with headers, scrolling, selection, and cell editing."""
        theme = ctk.ThemeManager.theme
        resolved_corner_radius = theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        resolved_border_width = theme["CTkFrame"]["border_width"] if border_width is None else border_width
        resolved_fg_color = theme["CTkFrame"]["fg_color"] if fg_color is None else fg_color
        resolved_border_color = theme["CTkFrame"]["border_color"] if border_color is None else border_color

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

        self._selection_manager = SelectionManager(
            target=selection_target,
            mode=selection_mode,
        )
        self._renderer = TableRenderer()

        self._headers: list[str] | None = None
        initial_cols = len(values[0]) if (values and len(values) > 0 and values[0]) else 0
        self._apply_headers(headers, initial_cols=initial_cols)
        self._show_headers: bool = (headers is not None) if show_headers is None else bool(show_headers)

        # Colors, fonts, alignment, and per-column setting lookup
        self._style = StyleResolver(
            options={
                "font": font,
                "header_font": header_font,
                "text_color": text_color,
                "header_text_color": header_text_color,
                "selected_color": selected_color,
                "selected_text_color": selected_text_color,
                "header_fg_color": header_fg_color,
                "row_color": row_color,
                "alternate_row_color": alternate_row_color,
                "header_hover_color": header_hover_color,
                "justify": justify,
                "header_alignment": header_alignment,
            },
            divider_color=resolved_border_color,
            get_headers=lambda: self._headers,
            get_total_cols=self._get_total_cols,
            get_frame_color=lambda: self._fg_color,
            apply_font_scaling=self._apply_font_scaling,
        )

        # Core Collaborator Engines
        self._raw_sort_key = sort_key
        self._data_model = TableDataModel(
            values=values,
            sort_key=self._normalize_sort_key_for_model(sort_key),
        )

        # Value formatting rules
        self._raw_formatters = formatters
        self._formatter_default: Callable[[Any], Any] | None = None
        self._formatter_cols: dict[int, Callable[[Any], Any]] = {}
        self._set_formatter_rules(formatters)

        # Column visibility, widths, geometry, and auto-fit
        self._layout_mgr = ColumnLayoutManager(
            self,
            self._data_model,
            show_columns=show_columns,
            column_widths=column_widths,
            get_total_cols=self._get_total_cols,
            get_headers=lambda: self._headers,
            get_canvas_width=lambda: self._table_canvas.winfo_width(),
            normalize_scoped_dict=self._style.normalize_scoped_dict,
            resolve_col_index=self._style.resolve_col_index,
            create_text_measure_lookup=self._style.create_text_measure_lookup,
            on_layout_changed=self._redraw,
            is_column_sortable=lambda c: self.is_column_sortable(c),
            format_cell=self._format_cell,
        )

        # Editing rules
        self._editable_default: bool = False
        self._editable_cols: dict[int, bool] = {}
        self._raw_editable = editable
        self._set_editable_rules(editable)
        self.on_cell_edit: Callable[[int, int, Any, Any], None] | None = on_cell_edit

        self._row_height: int = max(MIN_ROW_HEIGHT, row_height)
        self._header_height: int = max(MIN_HEADER_HEIGHT, header_height)
        self.command: Callable[[Any], None] | None = command
        self._copyable: bool = copyable

        # Grid, header and body canvases, scrollbars, and corner fillers
        self._create_widgets()

        # Scroll position, mouse wheel, and scrollbar handling
        self._scroll_controller = self._create_scroll_controller()

        # In-place cell editing text box
        self._editor = CellEditor(
            canvas=self._table_canvas,
            on_commit=self._commit_edit,
            on_cancel=self._cancel_edit,
        )

        # Keyboard navigation and shortcuts
        self._keyboard_router = self._create_keyboard_router()

        # Header hover, click sorting, and divider dragging
        self._header_controller = self._create_header_controller(header_sortable)

        self._option_setters = self._create_option_setters()
        self._option_getters = self._create_option_getters()

        self._re_grid_components()
        self._setup_event_bindings()
        self._update_colors()

    # -------------------------------------------------------------------------
    # Component Construction
    # -------------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the grid, the header and body canvases, the scrollbars, and the corner fillers."""
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._header_canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            height=scale(self, self._header_height),
        )
        self._header_corner = tk.Frame(self, highlightthickness=0, bd=0)
        self._table_canvas = tk.Canvas(self, highlightthickness=0, bd=0, takefocus=1)

        self._v_scrollbar = ctk.CTkScrollbar(self, orientation="vertical")
        self._h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal")
        self._bottom_corner = tk.Frame(self, highlightthickness=0, bd=0)

    def _create_scroll_controller(self) -> ScrollController:
        """Build the controller that tracks scroll position, mouse wheel, and scrollbars."""
        return ScrollController(
            self,
            self._table_canvas,
            self._header_canvas,
            self._v_scrollbar,
            self._h_scrollbar,
            self._data_model,
            self._layout_mgr,
            get_row_height=self._get_scaled_row_height,
            commit_edit=self._commit_edit,
            redraw=self._redraw,
            on_viewport_resized=self._on_viewport_resized,
        )

    def _create_keyboard_router(self) -> KeyboardRouter:
        """Build the router that turns key presses into focus moves, selections, edits, and copying."""
        return KeyboardRouter(
            self._data_model,
            self._selection_manager,
            self._layout_mgr,
            get_page_row_count=self._scroll_controller.get_page_row_count,
            is_editing=lambda: self._editor.is_editing,
            is_copyable=lambda: self._copyable,
            scroll_to=self._scroll_controller.scroll_to,
            start_editing=self._start_editing,
            cancel_edit=self._cancel_edit,
            select_all=self.select_all,
            clear_selection=self.clear_selection,
            copy_selection=self.copy_selection,
            notify_selection_changed=self._notify_command,
            redraw=self._redraw,
        )

    def _create_header_controller(self, header_sortable: bool | dict[int | str, bool]) -> HeaderController:
        """Build the controller that handles header hover, click sorting, and divider dragging."""
        return HeaderController(
            self,
            self._header_canvas,
            self._data_model,
            self._layout_mgr,
            header_sortable=header_sortable,
            normalize_scoped_dict=self._style.normalize_scoped_dict,
            is_header_visible=lambda: self._show_headers,
            has_hover_color=lambda: self._style.has_header_hover_color,
            get_canvas_width=lambda: self._table_canvas.winfo_width(),
            get_scroll_x=lambda: self._scroll_controller.scroll_x,
            sort_by=lambda col, ascending: self.sort_by(col, ascending=ascending),
            clear_sort=self.clear_sort,
            redraw_header=self._redraw_header,
            redraw=self._redraw,
        )

    # -------------------------------------------------------------------------
    # Event Bindings Setup
    # -------------------------------------------------------------------------

    def _setup_event_bindings(self) -> None:
        """Register mouse, keyboard, resize, and edit handlers across canvases."""
        self._scroll_controller.bind_events()

        self._table_canvas.bind("<Button-1>", self._on_body_click)
        self._table_canvas.bind("<Double-Button-1>", self._on_body_double_click)

        self._keyboard_router.bind_to(self._table_canvas)

        self._header_controller.bind_events()

    # -------------------------------------------------------------------------
    # Scoped Attribute Normalization
    # -------------------------------------------------------------------------

    def _normalize_sort_key_for_model(self, sort_key: Any) -> Any:
        """Translate header title keys in sort_key dictionary to logical column indexes."""
        if isinstance(sort_key, dict):
            default_val, resolved = self._style.normalize_scoped_dict(sort_key)
            result: dict[int | str, Any] = dict(resolved)
            if default_val is not None:
                result["default"] = default_val
            return result
        return sort_key

    def _re_normalize_scoped_attributes(self) -> None:
        """Re-normalize active scoped attribute dictionaries whenever headers change."""
        self._layout_mgr.reapply_show_columns_rules()
        self._set_formatter_rules(self._raw_formatters)
        self._set_editable_rules(self._raw_editable)
        self._header_controller.reapply_sortable_rules()
        self._style.update_colors()
        self._style.update_fonts()
        self._data_model.set_sort_key_rules(self._normalize_sort_key_for_model(self._raw_sort_key))

    def _update_colors(self) -> None:
        """Refresh the ready-to-draw colors and repaint the canvas backgrounds to match the frame."""
        self._style.update_colors()
        canvas_bg = self._style.get_canvas_background()
        for surface in (self._table_canvas, self._header_canvas, self._header_corner, self._bottom_corner):
            surface.configure(bg=canvas_bg)

    @override
    def _set_appearance_mode(self, mode_string: str) -> None:
        """Update colors and repaint the table when the appearance mode changes."""
        super()._set_appearance_mode(mode_string)
        self._update_colors()
        self._redraw()

    @override
    def _set_scaling(self, *args: Any, **kwargs: Any) -> None:
        """Update font scaling, layout positions, and repaint when the display scale changes."""
        super()._set_scaling(*args, **kwargs)
        self._style.update_fonts()
        self._re_grid_components()
        self._redraw()

    def _apply_headers(self, headers: list[str] | dict[int | str, str] | None, initial_cols: int = 0) -> None:
        """Apply or patch header titles from a list, dictionary, or None."""
        if headers is None:
            self._headers = None
            return

        if isinstance(headers, (list, tuple)):
            self._headers = [str(h) for h in headers]
            return

        if isinstance(headers, dict):
            if self._headers is not None:
                new_headers = list(self._headers)
                if "default" in headers:
                    new_headers = [str(headers["default"])] * len(new_headers)
            else:
                total_cols = max(initial_cols, self._get_total_cols())
                max_key = -1
                for k in headers:
                    if str(k).lower() != "default":
                        try:
                            max_key = max(max_key, int(k))
                        except (ValueError, TypeError):
                            pass
                needed = max(total_cols, max_key + 1)
                default_title = str(headers.get("default", ""))
                new_headers = [default_title] * needed

            for k, v in headers.items():
                if str(k).lower() == "default":
                    continue
                try:
                    idx = int(k)
                    if idx >= len(new_headers):
                        new_headers.extend([""] * (idx + 1 - len(new_headers)))
                    if 0 <= idx < len(new_headers):
                        new_headers[idx] = str(v)
                except (ValueError, TypeError):
                    pass

            self._headers = new_headers

    def _get_border_spacing(self) -> int:
        """Calculate the total scaled outer border gap in pixels."""
        border = int(self._border_width) if self._border_width else 0
        raw_spacing = self._border_spacing + border
        return scale(self, raw_spacing)

    def _re_grid_components(self) -> None:
        """Place the header canvas, body canvas, scrollbars, and filler corners into the grid."""
        spacing = self._get_border_spacing()

        if self._show_headers:
            self._header_canvas.grid(row=0, column=0, sticky="nsew", padx=(spacing, 0), pady=(spacing, 0))
            self._header_corner.grid(row=0, column=1, sticky="nsew", padx=(0, spacing), pady=(spacing, 0))
            body_pady = (0, 0)
        else:
            self._header_canvas.grid_remove()
            self._header_corner.grid_remove()
            body_pady = (spacing, 0)

        self._table_canvas.grid(row=1, column=0, sticky="nsew", padx=(spacing, 0), pady=body_pady)
        self._v_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, spacing), pady=body_pady)
        self._h_scrollbar.grid(row=2, column=0, sticky="ew", padx=(spacing, 0), pady=(0, spacing))
        self._bottom_corner.grid(row=2, column=1, sticky="nsew", padx=(0, spacing), pady=(0, spacing))

    def _get_scaled_row_height(self) -> int:
        """Calculate the scaled height of a table row in pixels."""
        return scale(self, self._row_height)

    def _get_scaled_header_height(self) -> int:
        """Calculate the scaled height of the header row in pixels."""
        return scale(self, self._header_height)

    def _get_total_cols(self) -> int:
        """Return the total number of columns defined by headers or dataset values."""
        if self._headers is not None:
            return len(self._headers)
        if hasattr(self, "_data_model") and self._data_model.row_count > 0 and self._data_model.values[0]:
            return len(self._data_model.values[0])
        return 0

    # -------------------------------------------------------------------------
    # Scrolling & Viewport Positioning
    # -------------------------------------------------------------------------

    def _on_viewport_resized(self) -> None:
        """Resize the header to match its configured height and repaint after the body canvas changes size."""
        self._header_canvas.configure(height=self._get_scaled_header_height())
        self._redraw()

    def scroll_to(self, row: int | None = None, col: int | str | None = None) -> None:
        """Scroll the view automatically so a specific row or column is visible on screen."""
        resolved_col = self._style.resolve_col_index(col) if col is not None else None
        if row is None and col is not None and resolved_col is None:
            return
        self._scroll_controller.scroll_to(row, resolved_col)

    # -------------------------------------------------------------------------
    # In-Place Editing Lifecycle
    # -------------------------------------------------------------------------

    def _set_formatter_rules(
        self,
        formatters: Callable[[Any], Any] | dict[int | str, Callable[[Any], Any]] | None,
    ) -> None:
        """Update column formatters, mapping header titles to logical column indexes."""
        self._raw_formatters = formatters
        if callable(formatters):
            self._formatter_default = formatters
            self._formatter_cols.clear()
        elif isinstance(formatters, dict):
            default_val, resolved = self._style.normalize_scoped_dict(formatters)
            self._formatter_default = default_val if callable(default_val) else None
            self._formatter_cols = {k: v for k, v in resolved.items() if callable(v)}
        else:
            self._formatter_default = None
            self._formatter_cols.clear()

    def _has_formatter(self, col: int) -> bool:
        """Return whether a column has a custom formatter assigned."""
        return col in self._formatter_cols or self._formatter_default is not None

    def _format_cell(self, col: int, value: Any) -> str:
        """Transform a raw cell value using the column's formatter, falling back to str()."""
        formatter = self._formatter_cols.get(col, self._formatter_default)
        if formatter is not None:
            try:
                res = formatter(value)
                return "" if res is None else str(res)
            except Exception:
                return str(value)
        return str(value)

    def _set_editable_rules(self, editable: bool | dict[int | str, bool]) -> None:
        """Update editable state, preserving baseline when 'default' is omitted in incremental dict reconfigures."""
        self._raw_editable = editable
        if isinstance(editable, dict):
            default_val, resolved = self._style.normalize_scoped_dict(editable)
            if default_val is not None:
                self._editable_default = bool(default_val)
            for k, v in resolved.items():
                self._editable_cols[k] = bool(v)
        else:
            self._editable_default = bool(editable)
            self._editable_cols.clear()

    def _has_editable_cells(self) -> bool:
        """Check whether at least one column permits cell editing."""
        total_cols = self._get_total_cols()
        if total_cols == 0:
            return self._editable_default
        return any(self._is_column_editable(c) for c in range(total_cols))

    def _is_column_editable(self, col: int) -> bool:
        """Check whether users are allowed to edit cells in this column."""
        if col in self._editable_cols:
            return self._editable_cols[col]
        if self._has_formatter(col):
            return False
        return self._editable_default

    def _start_editing(self, visual_row: int, col: int) -> None:
        """Open a floating text box over the target cell so the user can type."""
        if not self._is_column_editable(col):
            return
        if not (0 <= visual_row < self._data_model.row_count and 0 <= col < self._get_total_cols()):
            return

        self._commit_edit()
        self.scroll_to(row=visual_row, col=col)

        canvas_width = self._table_canvas.winfo_width()
        visible_cols = self._layout_mgr.get_visible_columns()
        if col not in visible_cols:
            return
        col_widths, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
        v_idx = visible_cols.index(col)
        scaled_row = self._get_scaled_row_height()

        x_left = col_offsets[v_idx] - self._scroll_controller.scroll_x
        col_w = col_widths[v_idx]
        y_top = visual_row * scaled_row - self._scroll_controller.scroll_y

        try:
            current_val = str(self._data_model.get_cell(visual_row, col))
        except IndexError:
            current_val = ""

        border_color_hex = self._style.colors["selected_bg"]
        cell_font = self._style.get_column_font(col)
        cell_align = self._style.get_column_alignments().get(col, "left")

        self._editor.start_editing(
            display_row=visual_row,
            col_index=col,
            initial_value=current_val,
            x_left=x_left,
            y_top=y_top,
            width=col_w,
            height=scaled_row,
            font=cell_font,
            border_color=border_color_hex,
            justify=cell_align,  # type: ignore[arg-type]
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
            old_val, row_id = self._data_model.update_cell(visual_r, c, new_val)

            # Freeze current visual order if editing the active sort column
            if self._data_model.sort_column == c:
                self._data_model.freeze_sort()

            if self.on_cell_edit is not None:
                self.on_cell_edit(row_id, c, old_val, new_val)

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
        visible_cols = self._layout_mgr.get_visible_columns()
        _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
        scaled_row = self._get_scaled_row_height()

        row = int((pixel_y + self._scroll_controller.scroll_y) // scaled_row)
        v_idx = bisect_right(col_offsets, pixel_x + self._scroll_controller.scroll_x) - 1

        if 0 <= row < self._data_model.row_count and 0 <= v_idx < len(visible_cols):
            return (row, visible_cols[v_idx])
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

        self._selection_manager.apply_click(clicked_r, clicked_c, is_ctrl=is_ctrl, is_shift=is_shift)
        self._notify_command()
        self._redraw()

    def _on_body_double_click(self, event: Any) -> None:
        """Open the cell editor when the user double-clicks a cell."""
        self._commit_edit()
        if not self._has_editable_cells():
            return

        cell = self._get_cell_at(event.x, event.y)
        if cell is not None:
            self._start_editing(cell[0], cell[1])

    def _notify_command(self) -> None:
        """Fire the user-provided selection callback with current selected items."""
        if self.command:
            selected = (
                self.get_selected_rows() if self._selection_manager.target == "row" else self.get_selected_cells()
            )
            self.command(selected)

    # -------------------------------------------------------------------------
    # Column Auto-Fit
    # -------------------------------------------------------------------------

    def auto_fit_columns(self, columns: list[int | str] | None = None) -> None:
        """Calculate and snap column widths to fit content in a single batched pass."""
        self._layout_mgr.auto_fit_columns(columns)

    def auto_fit_column(self, col_index: int | str) -> None:
        """Calculate and snap column width to fit header and cell text without locking other columns."""
        self._layout_mgr.auto_fit_column(col_index)

    # -------------------------------------------------------------------------
    # Viewport Redraw Orchestrator
    # -------------------------------------------------------------------------

    def _redraw_header(self) -> None:
        """Render the pinned table header bar with column dividers, sort glyphs, and hover highlights."""
        if not self._show_headers:
            return

        canvas_w = self._table_canvas.winfo_width()
        if canvas_w <= 1:
            return

        visible_cols = self._layout_mgr.get_visible_columns()
        col_widths, col_offsets = self._layout_mgr.calculate_geometry(canvas_w)
        total_cols = len(col_widths)
        if total_cols == 0:
            self._header_canvas.delete("all")
            return

        start_col = max(0, bisect_right(col_offsets, self._scroll_controller.scroll_x) - 1 - self._overscan_cols)
        end_col = min(
            total_cols,
            bisect_left(col_offsets, self._scroll_controller.scroll_x + canvas_w) + 1 + self._overscan_cols,
        )

        scaled_padding = scale(self, CELL_HORIZONTAL_PADDING)
        divider_hex = self._style.colors["divider"]
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
            scroll_x=self._scroll_controller.scroll_x,
            header_height=header_h,
            canvas_width=canvas_w,
            corner_radius=scaled_radius,
            bg_hex=self._style.colors["header_fg"],
            text_color_hex=self._style.colors["header_text"],
            divider_color_hex=divider_hex,
            header_font=self._style.get_scaled_header_font(),
            sort_col=self._data_model.sort_column,
            sort_ascending=self._data_model.sort_ascending,
            scaled_padding=scaled_padding,
            header_alignments=self._style.get_header_alignments(),
            header_text_colors=self._style.header_text_colors,
            header_fonts=self._style.header_fonts,
            header_font_objs=self._style.header_font_objs,
            hovered_col=self._header_controller.hovered_col,
            header_hover_color_hex=self._style.colors.get("header_hover"),
            visible_cols=visible_cols,
        )

    def _redraw(self) -> None:
        """Synchronize header, body viewport, and scrollbars."""
        canvas_w = self._table_canvas.winfo_width()
        canvas_h = self._table_canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        visible_cols = self._layout_mgr.get_visible_columns()
        col_widths, col_offsets = self._layout_mgr.calculate_geometry(canvas_w)
        total_cols = len(col_widths)
        total_rows = self._data_model.row_count
        total_content_width = col_offsets[-1]

        if total_cols > 0:
            start_col = max(0, bisect_right(col_offsets, self._scroll_controller.scroll_x) - 1 - self._overscan_cols)
            end_col = min(
                total_cols,
                bisect_left(col_offsets, self._scroll_controller.scroll_x + canvas_w) + 1 + self._overscan_cols,
            )
        else:
            start_col, end_col = 0, 0

        scaled_padding = scale(self, CELL_HORIZONTAL_PADDING)
        divider_hex = self._style.colors["divider"]

        # Pinned header rendering
        if self._show_headers:
            self._redraw_header()

        # Body viewport rendering
        scaled_row = self._get_scaled_row_height()
        total_content_height = total_rows * scaled_row

        start_row = max(0, int(self._scroll_controller.scroll_y // scaled_row) - self._overscan_rows)
        end_row = min(
            total_rows,
            int((self._scroll_controller.scroll_y + canvas_h) // scaled_row) + self._overscan_rows + 1,
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
            scroll_x=self._scroll_controller.scroll_x,
            scroll_y=self._scroll_controller.scroll_y,
            scaled_row_height=scaled_row,
            canvas_width=canvas_w,
            text_color_hex=self._style.colors["text"],
            selected_bg_hex=self._style.colors["selected_bg"],
            selected_text_hex=self._style.colors["selected_text"],
            row_even_bg=self._style.colors["row_even"],
            row_odd_bg=self._style.colors["row_odd"],
            divider_color_hex=divider_hex,
            body_font=self._style.get_scaled_body_font(),
            scaled_padding=scaled_padding,
            column_alignments=self._style.get_column_alignments(),
            col_text_colors=self._style.column_text_colors,
            col_fonts=self._style.column_fonts,
            col_font_objs=self._style.column_font_objs,
            visible_cols=visible_cols,
            resolve_color=self._style.resolve_color,
            format_cell=self._format_cell,
        )

        # Synchronize scrollbars
        self._renderer.sync_scrollbars(
            v_scrollbar=self._v_scrollbar,
            h_scrollbar=self._h_scrollbar,
            scroll_x=self._scroll_controller.scroll_x,
            scroll_y=self._scroll_controller.scroll_y,
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
        self._selection_manager.select_cell(row_index, col_index, self._data_model.row_count, total_cols)
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
        tsv_data = self._selection_manager.export_tsv(self._data_model, format_cell=self._format_cell)
        if tsv_data:
            with suppress(tk.TclError):
                root = self.winfo_toplevel()
                root.clipboard_clear()
                root.clipboard_append(tsv_data)
        return tsv_data

    def get(self, row: int | None = None, column: int | str | None = None) -> Any:
        """Return table data in current visual display order."""
        if row is not None:
            if column is not None:
                return self.get_cell(row, column)
            return self.get_row(row)

        if column is not None:
            c = self._style.resolve_col_index(column)
            if c is None:
                raise IndexError(f"Column '{column}' not found")
            total_cols = self._get_total_cols()
            if not (0 <= c < total_cols):
                raise IndexError(f"Column index {column} out of range [0, {total_cols})")
            return [self._data_model.get_cell(r, c) for r in range(self._data_model.row_count)]

        return self._data_model.get_all_rows()

    def get_row(self, row_index: int) -> list[Any]:
        """Return the record values at display index row_index."""
        return self._data_model.get_row(row_index)

    @overload
    def get_row_id(self, display_row: int) -> int:
        """Translate a single visual display row index to its permanent row ID."""
        ...

    @overload
    def get_row_id(self, display_row: Sequence[int]) -> list[int]:
        """Translate multiple visual display row indexes to permanent row IDs."""
        ...

    def get_row_id(self, display_row: int | Sequence[int]) -> int | list[int]:
        """Translate one or multiple visual display row indexes to permanent row IDs."""
        if isinstance(display_row, (list, tuple, set)):
            return [self._data_model.get_row_id(r) for r in display_row]
        return self._data_model.get_row_id(display_row)

    @overload
    def get_display_row(self, row_id: int) -> int:
        """Translate a single permanent row ID to its current visual display index."""
        ...

    @overload
    def get_display_row(self, row_id: Sequence[int]) -> list[int]:
        """Translate multiple permanent row IDs to current visual display indexes."""
        ...

    def get_display_row(self, row_id: int | Sequence[int]) -> int | list[int]:
        """Translate one or multiple permanent row IDs to current visual display indexes."""
        if isinstance(row_id, (list, tuple, set)):
            return [self._data_model.get_display_row(r) for r in row_id]
        return self._data_model.get_display_row(row_id)

    def get_row_by_id(self, row_id: int) -> list[Any]:
        """Return the record values matching a specific permanent row ID."""
        return self._data_model.get_row_by_id(row_id)

    def get_cell(self, row_index: int, col_index: int | str) -> Any:
        """Return the cell value at display row and column."""
        c = self._style.resolve_col_index(col_index)
        if c is None:
            raise IndexError(f"Column '{col_index}' not found")
        return self._data_model.get_cell(row_index, c)

    def get_cell_text_color(self, row_index: int, col_index: int | str) -> str | tuple[str, str] | None:
        """Return the custom text color assigned to a cell at display row and column."""
        c = self._style.resolve_col_index(col_index)
        if c is None:
            raise IndexError(f"Column '{col_index}' not found")
        return self._data_model.get_cell_text_color(row_index, c)

    def set_cell_text_color(
        self,
        row_index: int,
        col_index: int | str,
        color: str | tuple[str, str] | None,
        redraw: bool = True,
    ) -> None:
        """Assign or remove a custom text color for a specific cell at display row and column."""
        c = self._style.resolve_col_index(col_index)
        if c is None:
            raise IndexError(f"Column '{col_index}' not found")
        self._data_model.set_cell_text_color(row_index, c, color)
        if redraw:
            self._redraw()

    def clear_cell_text_colors(self, redraw: bool = True) -> None:
        """Remove all custom cell text colors."""
        self._data_model.clear_cell_text_colors()
        if redraw:
            self._redraw()

    def get_formatted_cell(self, row_index: int, col_index: int | str) -> str:
        """Return the formatted display text of a cell at display row and column."""
        c = self._style.resolve_col_index(col_index)
        if c is None:
            raise IndexError(f"Column '{col_index}' not found")
        val = self._data_model.get_cell(row_index, c)
        return self._format_cell(c, val)

    def get_column_formatter(self, column: int | str) -> Callable[[Any], Any] | None:
        """Return the custom formatter function assigned to a column."""
        c = self._style.resolve_col_index(column)
        if c is None:
            raise IndexError(f"Column '{column}' not found")
        return self._formatter_cols.get(c, self._formatter_default)

    def set_column_formatter(
        self,
        column: int | str,
        formatter: Callable[[Any], Any] | None,
        redraw: bool = True,
    ) -> None:
        """Assign or remove a custom display formatter for a specific column."""
        c = self._style.resolve_col_index(column)
        if c is None:
            raise IndexError(f"Column '{column}' not found")
        if formatter is None:
            self._formatter_cols.pop(c, None)
        else:
            self._formatter_cols[c] = formatter
        if not self._is_column_editable(c) and self.is_editing:
            self._cancel_edit()
        if redraw:
            self._redraw()

    def clear_column_formatters(self, redraw: bool = True) -> None:
        """Remove all custom column formatters."""
        self._raw_formatters = None
        self._formatter_default = None
        self._formatter_cols.clear()
        if redraw:
            self._redraw()

    def update_cell(self, row_index: int, col_index: int | str, value: Any, notify: bool = True) -> None:
        """Update a specific cell value in-place, updating sorting if relevant."""
        c = self._style.resolve_col_index(col_index)
        if c is None:
            raise IndexError(f"Column '{col_index}' not found")
        old_val, row_id = self._data_model.update_cell(row_index, c, value)

        if self._data_model.sort_column == c:
            self.sort_by(c, ascending=self._data_model.sort_ascending)
        else:
            self._redraw()

        if notify and self.on_cell_edit is not None:
            self.on_cell_edit(row_id, c, old_val, value)

    def update_row(self, display_row: int, values: list[Any], notify: bool = True) -> None:
        """Update an entire row in-place, updating sorting if relevant."""
        if self._editor.is_editing and self._selection_manager.focused_row == display_row:
            self._cancel_edit()

        total_cols = self._get_total_cols()
        old_row, row_id = self._data_model.update_row(display_row, values, total_cols=total_cols)

        sort_col = self._data_model.sort_column
        if sort_col is not None and (
            sort_col >= len(old_row) or sort_col >= len(values) or old_row[sort_col] != values[sort_col]
        ):
            self.sort_by(sort_col, ascending=self._data_model.sort_ascending)
        else:
            self._redraw()

        if notify and self.on_cell_edit is not None:
            max_check = min(len(old_row), len(values))
            for c in range(max_check):
                if old_row[c] != values[c]:
                    self.on_cell_edit(row_id, c, old_row[c], values[c])

    def get_header(self, col_index: int) -> str:
        """Return the header title for a specific column index."""
        if self._headers is not None and 0 <= col_index < len(self._headers):
            return self._headers[col_index]
        return ""

    def set_header(self, col_index: int, title: str) -> None:
        """Set or update the title for a specific column header."""
        self.configure(headers={col_index: title})

    # Keep undocumented in public API guides
    def get_displayed_header(self, col_index: int | str) -> str:
        """Return the full header title currently displayed on screen, including any active sort arrow.

        Internal / Undocumented: Omit from public documentation and user guides.
        """
        c = self._style.resolve_col_index(col_index)
        if c is None:
            return ""
        base_title = self.get_header(c)
        if not base_title:
            return ""
        sort_col, is_asc = self.get_sort_state()
        if sort_col == c:
            glyph = "▲" if is_asc else "▼"
            return f"{base_title} {glyph}"
        return base_title

    def is_column_sortable(self, col_index: int | str) -> bool:
        """Return whether clicking the given column header is allowed to sort the table."""
        c = self._style.resolve_col_index(col_index)
        if c is None or not hasattr(self, "_header_controller"):
            return True
        return self._header_controller.is_column_sortable(c)

    def insert_row(self, index: int | None = None, values: list[Any] | None = None) -> int:
        """Insert a row at display position index (or append if None). Return the new display index."""
        self._cancel_edit()
        total_cols = self._get_total_cols()
        visual_insert_pos, new_row_id = self._data_model.insert_row(index, values, total_cols)

        self._selection_manager.adjust_indexes_after_insert(visual_insert_pos)

        if self._data_model.sort_column is not None:
            self.sort_by(self._data_model.sort_column, ascending=self._data_model.sort_ascending)
            # Re-locate the newly inserted row's visual slot after re-sorting
            visual_insert_pos = self._data_model.get_display_row(new_row_id)
        else:
            self._redraw()

        return visual_insert_pos

    def delete_rows(self, row_indexes: list[int] | set[int] | int) -> None:
        """Delete one or multiple display rows and adjust selection mappings."""
        self._cancel_edit()
        deleted_targets = self._data_model.delete_rows(row_indexes)
        if not deleted_targets:
            return

        self._selection_manager.adjust_indexes_after_delete(deleted_targets, self._data_model.row_count)

        self._scroll_controller.clamp_vertical()

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

    def freeze_sort(self) -> None:
        """Lock current visual sorted order into storage and reset sort state while preserving row IDs."""
        self._commit_edit()
        self._data_model.freeze_sort()
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
        if hasattr(self, "_option_getters"):
            getter = self._option_getters.get(attribute_name)
            if getter is not None:
                return getter()
        if hasattr(self, "_style") and attribute_name in STYLE_OPTIONS:
            return self._style.get_option(attribute_name)
        return super().cget(attribute_name)

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Configure widget options dynamically and refresh the viewport in a single batched pass."""
        needs_redraw = require_redraw
        re_grid = False

        for name, setter in self._option_setters.items():
            if name not in kwargs:
                continue
            setter(kwargs.pop(name))
            needs_redraw = needs_redraw or name in _REDRAW_OPTIONS
            re_grid = re_grid or name in _REGRID_OPTIONS

        style_options = {name: kwargs.pop(name) for name in STYLE_OPTIONS if name in kwargs}
        if style_options:
            self._style.configure_options(style_options)
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

    # -------------------------------------------------------------------------
    # Option Dispatch Tables
    # -------------------------------------------------------------------------

    def _create_option_getters(self) -> dict[str, Callable[[], Any]]:
        """Map each table-specific option name to the function that reads its current value."""
        return {
            "values": lambda: self._data_model.values,
            "headers": lambda: self._headers,
            "show_headers": lambda: self._show_headers,
            "show_columns": lambda: self._layout_mgr.show_columns_setting,
            "column_widths": lambda: self._layout_mgr.column_widths,
            "sort_key": lambda: self._data_model.sort_key,
            "header_sortable": lambda: self._header_controller.sortable_setting,
            "editable": self._get_editable_setting,
            "selection_target": lambda: self._selection_manager.target,
            "selection_mode": lambda: self._selection_manager.mode,
            "copyable": lambda: self._copyable,
            "row_height": lambda: self._row_height,
            "header_height": lambda: self._header_height,
            "border_spacing": lambda: self._border_spacing,
            "formatters": self._get_formatters_setting,
            "command": lambda: self.command,
        }

    def _create_option_setters(self) -> dict[str, Callable[[Any], None]]:
        """Map each table-specific option name to the function that applies a new value.

        The order matters: headers must be applied before the settings that
        refer to columns by header title.
        """
        return {
            "values": self._configure_values,
            "headers": self._configure_headers,
            "show_headers": self._configure_show_headers,
            "show_columns": self._configure_show_columns,
            "column_widths": self._configure_column_widths,
            "editable": self._configure_editable,
            "formatters": self._configure_formatters,
            "header_sortable": self._configure_header_sortable,
            "selection_target": self._selection_manager.set_target,
            "selection_mode": self._selection_manager.set_mode,
            "copyable": self._configure_copyable,
            "row_height": self._configure_row_height,
            "header_height": self._configure_header_height,
            "border_spacing": self._configure_border_spacing,
            "sort_key": self._configure_sort_key,
            "on_cell_edit": self._configure_on_cell_edit,
            "command": self._configure_command,
        }

    def _get_formatters_setting(
        self,
    ) -> Callable[[Any], Any] | dict[int | str, Callable[[Any], Any]] | None:
        """Return active formatter rules."""
        if not self._formatter_cols:
            return self._formatter_default
        rules: dict[int | str, Callable[[Any], Any]] = dict(self._formatter_cols)
        if self._formatter_default is not None:
            rules["default"] = self._formatter_default
        return rules

    def _configure_formatters(
        self,
        formatters: Callable[[Any], Any] | dict[int | str, Callable[[Any], Any]] | None,
    ) -> None:
        """Update column formatters and refresh the display."""
        self._set_formatter_rules(formatters)
        if not self._has_editable_cells():
            self._cancel_edit()

    def _get_editable_setting(self) -> bool | dict[int | str, bool]:
        """Return the editable rules as one bool, or as a per-column dict with a 'default' entry."""
        if not self._editable_cols:
            return self._editable_default
        rules: dict[int | str, bool] = dict(self._editable_cols)
        rules["default"] = self._editable_default
        return rules

    def _configure_values(self, new_values: list[list[Any]] | None) -> None:
        """Replace the whole dataset, then reset the selection and scroll back to the top."""
        self._commit_edit()
        self._data_model.reset_values(new_values)
        self._selection_manager.clear()
        self._scroll_controller.reset_vertical()

    def _configure_headers(self, new_headers: list[str] | dict[int | str, str] | None) -> None:
        """Apply new header titles and rebuild every setting that refers to columns by title.

        Headers are shown whenever titles exist. An explicit show_headers in the same
        configure call is applied afterwards and wins.
        """
        self._apply_headers(new_headers)
        self._show_headers = self._headers is not None
        self._re_normalize_scoped_attributes()

    def _configure_show_headers(self, show: bool) -> None:
        """Show or hide the header bar."""
        self._show_headers = bool(show)

    def _configure_show_columns(self, show_columns: bool | dict[int | str, bool]) -> None:
        """Change which columns are visible and scroll back to the left edge."""
        self._layout_mgr.set_show_columns_rules(show_columns)
        self._scroll_controller.reset_horizontal()

    def _configure_column_widths(self, column_widths: int | str | dict[int | str, int | str] | None) -> None:
        """Change column widths and scroll back to the left edge."""
        self._layout_mgr.column_widths = column_widths
        self._scroll_controller.reset_horizontal()

    def _configure_editable(self, editable: bool | dict[int | str, bool]) -> None:
        """Change which columns can be edited and close any open editor if none remain."""
        self._set_editable_rules(editable)
        if not self._has_editable_cells():
            self._cancel_edit()

    def _configure_header_sortable(self, header_sortable: bool | dict[int | str, bool]) -> None:
        """Change which column headers sort the table when clicked."""
        self._header_controller.set_sortable_rules(header_sortable)

    def _configure_copyable(self, copyable: bool) -> None:
        """Turn the Ctrl+C copy shortcut on or off."""
        self._copyable = bool(copyable)

    def _configure_row_height(self, row_height: int) -> None:
        """Set the body row height, never below the minimum."""
        self._row_height = max(MIN_ROW_HEIGHT, int(row_height))

    def _configure_header_height(self, header_height: int) -> None:
        """Set the header bar height, never below the minimum."""
        self._header_height = max(MIN_HEADER_HEIGHT, int(header_height))

    def _configure_border_spacing(self, border_spacing: int) -> None:
        """Set the gap between the frame border and the table contents, never below zero."""
        self._border_spacing = max(0, int(border_spacing))

    def _configure_sort_key(self, sort_key: Any) -> None:
        """Change how cell values are compared when sorting."""
        self._raw_sort_key = sort_key
        self._data_model.set_sort_key_rules(self._normalize_sort_key_for_model(sort_key))

    def _configure_on_cell_edit(self, callback: Callable[[int, int, Any, Any], None] | None) -> None:
        """Set the function called after a cell value changes."""
        self.on_cell_edit = callback

    def _configure_command(self, callback: Callable[[Any], None] | None) -> None:
        """Set the function called when the selection changes."""
        self.command = callback

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
