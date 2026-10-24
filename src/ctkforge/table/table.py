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

from ctkforge.geometry import scale
from ctkforge.table.canvas_renderer import TableRenderer
from ctkforge.table.cell_editor import CellEditor
from ctkforge.table.column_layout import ColumnLayoutManager, TextMeasureLookup
from ctkforge.table.constants import (
    CELL_HORIZONTAL_PADDING,
    DEFAULT_BORDER_SPACING,
    DEFAULT_HEADER_HEIGHT,
    DEFAULT_OVERSCAN_COLS,
    DEFAULT_OVERSCAN_ROWS,
    DEFAULT_ROW_HEIGHT,
    HORIZONTAL_SCROLL_STEP_PX,
    MIN_HEADER_HEIGHT,
    MIN_ROW_HEIGHT,
    MOUSEWHEEL_BASE_DELTA,
    MOUSEWHEEL_STEP_ROWS,
    TK_CONTROL_MASK,
    TK_SHIFT_MASK,
)
from ctkforge.table.data_model import TableDataModel
from ctkforge.table.header_controller import HeaderController
from ctkforge.table.keyboard_router import KeyboardRouter
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
        **kwargs: Any,
    ) -> None:
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

        # Core Collaborator Engines
        self._raw_sort_key = sort_key
        self._data_model = TableDataModel(
            values=values,
            sort_key=self._normalize_sort_key_for_model(sort_key),
        )

        # Column visibility, widths, geometry, and auto-fit
        self._layout_mgr = ColumnLayoutManager(
            self,
            self._data_model,
            show_columns=show_columns,
            column_widths=column_widths,
            get_total_cols=self._get_total_cols,
            get_headers=lambda: self._headers,
            get_canvas_width=lambda: self._table_canvas.winfo_width(),
            normalize_scoped_dict=self._normalize_scoped_dict,
            resolve_col_index=self._resolve_col_index,
            create_text_measure_lookup=self._create_text_measure_lookup,
            on_layout_changed=self._redraw,
        )

        # Column body styling
        self._justify = justify
        self._header_alignment = header_alignment
        self._header_hover_color = header_hover_color

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

        # Typography & Color tokens
        self._font: tuple[str, int] | ctk.CTkFont = ctk.CTkFont() if font is None else font
        self._header_font: tuple[str, int] | ctk.CTkFont = (
            ctk.CTkFont(weight="bold") if header_font is None else header_font
        )
        self._text_color: Any = theme["CTkLabel"]["text_color"] if text_color is None else text_color
        self._header_text_color: Any = (
            theme["CTkLabel"]["text_color"] if header_text_color is None else header_text_color
        )
        self._selected_color: str | tuple[str, str] = (
            theme["CTkButton"]["fg_color"] if selected_color is None else selected_color
        )
        self._selected_text_color: str | tuple[str, str] = (
            theme["CTkButton"]["text_color"] if selected_text_color is None else selected_text_color
        )
        self._header_fg_color: str | tuple[str, str] | list[str] = (
            theme["CTkFrame"].get("top_fg_color", theme["CTkFrame"]["fg_color"])
            if header_fg_color is None
            else header_fg_color
        )
        self._row_color: str | tuple[str, str] | None = row_color
        self._alternate_row_color: str | tuple[str, str] | None = alternate_row_color
        self._divider_color: str | tuple[str, str] | list[str] = (
            border_color if border_color is not None else theme["CTkFrame"]["border_color"]
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

        self._v_scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self._on_v_scrollbar_command)
        self._h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self._on_h_scrollbar_command)
        self._bottom_corner = tk.Frame(self, highlightthickness=0, bd=0)

        self._editor = CellEditor(
            canvas=self._table_canvas,
            on_commit=self._commit_edit,
            on_cancel=self._cancel_edit,
        )

        # Keyboard navigation and shortcuts
        self._keyboard_router = KeyboardRouter(
            self._data_model,
            self._selection_manager,
            self._layout_mgr,
            get_page_row_count=self._get_page_row_count,
            is_editing=lambda: self._editor.is_editing,
            is_copyable=lambda: self._copyable,
            scroll_to=lambda row, col: self.scroll_to(row=row, col=col),
            start_editing=self._start_editing,
            cancel_edit=self._cancel_edit,
            select_all=self.select_all,
            clear_selection=self.clear_selection,
            copy_selection=self.copy_selection,
            notify_selection_changed=self._notify_command,
            redraw=self._redraw,
        )

        # Header hover, click sorting, and divider dragging
        self._header_controller = HeaderController(
            self,
            self._header_canvas,
            self._data_model,
            self._layout_mgr,
            header_sortable=header_sortable,
            normalize_scoped_dict=self._normalize_scoped_dict,
            is_header_visible=lambda: self._show_headers,
            has_hover_color=lambda: self._header_hover_color is not None,
            get_canvas_width=lambda: self._table_canvas.winfo_width(),
            get_scroll_x=lambda: self._scroll_x,
            sort_by=lambda col, ascending: self.sort_by(col, ascending=ascending),
            clear_sort=self.clear_sort,
            redraw_header=self._redraw_header,
            redraw=self._redraw,
        )

        # Pre-resolved color and font caches for high performance
        self._cached_colors: dict[str, str] = {}
        self._cached_col_text_colors: dict[int, str] = {}
        self._cached_header_text_colors: dict[int, str] = {}
        self._cached_col_fonts: dict[int, Any] = {}
        self._cached_col_font_objs: dict[int, tkfont.Font] = {}
        self._cached_header_fonts: dict[int, Any] = {}
        self._cached_header_font_objs: dict[int, tkfont.Font] = {}

        self._re_grid_components()
        self._setup_event_bindings()
        self._update_colors()
        self._update_fonts()

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

        self._keyboard_router.bind_to(self._table_canvas)

        self._header_controller.bind_events()

    # -------------------------------------------------------------------------
    # Color & Layout Configuration
    # -------------------------------------------------------------------------

    def _resolve_color(self, color: Any) -> str:
        """Resolve a CustomTkinter light/dark color tuple into a hex string for Tk canvas."""
        if color is None:
            return ""
        if isinstance(color, dict):
            return self._resolve_color(color.get("default", ""))
        if isinstance(color, (tuple, list)):
            mode = ctk.get_appearance_mode()
            return color[1] if mode == "Dark" else color[0]
        return str(color)

    def _update_colors(self) -> None:
        """Synchronize raw Tkinter canvas backgrounds and cache resolved theme colors."""
        canvas_bg = self._resolve_color(self._fg_color)
        if not canvas_bg or canvas_bg == "transparent":
            canvas_bg = self._resolve_color(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self._table_canvas.configure(bg=canvas_bg)
        self._header_canvas.configure(bg=canvas_bg)
        self._header_corner.configure(bg=canvas_bg)
        self._bottom_corner.configure(bg=canvas_bg)

        base_color = self._row_color if self._row_color is not None else self._fg_color
        alt_color = self._alternate_row_color if self._alternate_row_color is not None else base_color

        default_text_color = self._text_color
        if isinstance(self._text_color, dict):
            default_text_color = self._text_color.get("default", ctk.ThemeManager.theme["CTkLabel"]["text_color"])

        default_header_text_color = self._header_text_color
        if isinstance(self._header_text_color, dict):
            default_header_text_color = self._header_text_color.get(
                "default", ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            )

        self._cached_colors = {
            "header_fg": self._resolve_color(self._header_fg_color),
            "header_text": self._resolve_color(default_header_text_color),
            "divider": self._resolve_color(self._divider_color),
            "text": self._resolve_color(default_text_color),
            "selected_bg": self._resolve_color(self._selected_color),
            "selected_text": self._resolve_color(self._selected_text_color),
            "row_even": self._resolve_color(base_color),
            "row_odd": self._resolve_color(alt_color),
        }
        if self._header_hover_color is not None:
            self._cached_colors["header_hover"] = self._resolve_color(self._header_hover_color)
        else:
            self._cached_colors.pop("header_hover", None)

        # Pre-resolve per-column and per-header text colors into hex strings
        self._cached_col_text_colors = {
            c: self._resolve_color(col) for c, col in self._get_normalized_column_text_colors().items()
        }
        self._cached_header_text_colors = {
            c: self._resolve_color(col) for c, col in self._get_normalized_header_text_colors().items()
        }

    def _resolve_font_descriptor(
        self,
        raw_font: Any,
        base_font: tuple[str, int] | ctk.CTkFont,
    ) -> Any:
        """Resolve font shortcuts ('bold', 'italic') into CTkFont instances or return font unmodified."""
        if isinstance(raw_font, str):
            shortcut = raw_font.lower().strip()
            if shortcut in ("bold", "italic", "bold italic", "bold_italic"):
                family = "TkDefaultFont"
                size = 13
                if isinstance(base_font, ctk.CTkFont):
                    family = base_font.cget("family")
                    size = base_font.cget("size")
                elif isinstance(base_font, (tuple, list)) and len(base_font) >= 2:
                    family = str(base_font[0])
                    size = int(base_font[1])

                is_bold = "bold" in shortcut
                is_italic = "italic" in shortcut
                return ctk.CTkFont(
                    family=family,
                    size=size,
                    weight="bold" if is_bold else "normal",
                    slant="italic" if is_italic else "roman",
                )
        return raw_font

    def _get_base_font(self) -> tuple[str, int] | ctk.CTkFont:
        if isinstance(self._font, dict) and "default" in self._font:
            return self._font["default"]
        if isinstance(self._font, (ctk.CTkFont, tuple)):
            return self._font
        return ctk.CTkFont()

    def _get_base_header_font(self) -> tuple[str, int] | ctk.CTkFont:
        if isinstance(self._header_font, dict) and "default" in self._header_font:
            return self._header_font["default"]
        if isinstance(self._header_font, (ctk.CTkFont, tuple)):
            return self._header_font
        return ctk.CTkFont(weight="bold")

    def _update_fonts(self) -> None:
        """Cache resolved scaled fonts and measurement objects for column and header viewports."""
        self._cached_col_fonts.clear()
        self._cached_col_font_objs.clear()
        self._cached_header_fonts.clear()
        self._cached_header_font_objs.clear()

        base_font = self._get_base_font()
        base_header_font = self._get_base_header_font()

        # Cache column body fonts
        normalized_col_fonts = self._get_normalized_column_fonts()
        for c, raw_f in normalized_col_fonts.items():
            resolved = self._resolve_font_descriptor(raw_f, base_font)
            scaled_f = self._apply_font_scaling(resolved)
            self._cached_col_fonts[c] = scaled_f
            self._cached_col_font_objs[c] = tkfont.Font(font=scaled_f)

        # Cache header fonts
        normalized_header_fonts = self._get_normalized_header_fonts()
        for c, raw_hf in normalized_header_fonts.items():
            resolved = self._resolve_font_descriptor(raw_hf, base_header_font)
            scaled_hf = self._apply_font_scaling(resolved)
            self._cached_header_fonts[c] = scaled_hf
            self._cached_header_font_objs[c] = tkfont.Font(font=scaled_hf)

    def _resolve_col_index(self, key: int | str) -> int | None:
        """Resolve an integer index or header title string into a logical column index."""
        if isinstance(key, int):
            return key
        if str(key).lower() == "default":
            return None
        try:
            return int(key)
        except (ValueError, TypeError):
            if self._headers is not None and key in self._headers:
                return self._headers.index(key)
            return None

    def _normalize_scoped_dict[T](
        self,
        mapping: dict[int | str, T] | None,
    ) -> tuple[T | None, dict[int, T]]:
        """Split a scoped attribute dict into an optional default value and resolved {col_idx: value} pairs."""
        if not isinstance(mapping, dict):
            return None, {}

        default_val: T | None = None
        resolved: dict[int, T] = {}

        for raw_k, v in mapping.items():
            if str(raw_k).lower() == "default":
                default_val = v
                continue

            idx = self._resolve_col_index(raw_k)
            if idx is not None:
                resolved[idx] = v

        return default_val, resolved

    def _get_normalized_column_alignments(self) -> dict[int, str]:
        total_cols = self._get_total_cols()
        attr = self._justify
        if isinstance(attr, str):
            align = attr.lower()
            if align in ("left", "center", "right"):
                return {c: align for c in range(total_cols)}
        if isinstance(attr, dict):
            default_val, resolved = self._normalize_scoped_dict(attr)
            res: dict[int, str] = {}
            if default_val is not None and str(default_val).lower() in ("left", "center", "right"):
                res = {c: str(default_val).lower() for c in range(total_cols)}
            for c, v in resolved.items():
                if isinstance(v, str) and v.lower() in ("left", "center", "right"):
                    res[c] = v.lower()
            return res
        return {}

    def _get_normalized_header_alignments(self) -> dict[int, str]:
        total_cols = self._get_total_cols()
        if isinstance(self._header_alignment, str):
            align = self._header_alignment.lower()
            if align in ("left", "center", "right"):
                return {c: align for c in range(total_cols)}
        if isinstance(self._header_alignment, dict):
            default_val, resolved = self._normalize_scoped_dict(self._header_alignment)
            res: dict[int, str] = {}
            if default_val is not None and str(default_val).lower() in ("left", "center", "right"):
                res = {c: str(default_val).lower() for c in range(total_cols)}
            for c, v in resolved.items():
                if isinstance(v, str) and v.lower() in ("left", "center", "right"):
                    res[c] = v.lower()
            return res
        return {}

    def _get_normalized_column_text_colors(self) -> dict[int, Any]:
        if isinstance(self._text_color, dict):
            _, resolved = self._normalize_scoped_dict(self._text_color)
            return resolved
        return {}

    def _get_normalized_header_text_colors(self) -> dict[int, Any]:
        if isinstance(self._header_text_color, dict):
            _, resolved = self._normalize_scoped_dict(self._header_text_color)
            return resolved
        return {}

    def _get_normalized_column_fonts(self) -> dict[int, Any]:
        if isinstance(self._font, dict):
            _, resolved = self._normalize_scoped_dict(self._font)
            return resolved
        return {}

    def _get_normalized_header_fonts(self) -> dict[int, Any]:
        if isinstance(self._header_font, dict):
            _, resolved = self._normalize_scoped_dict(self._header_font)
            return resolved
        return {}

    def _normalize_sort_key_for_model(self, sort_key: Any) -> Any:
        """Translate header title keys in sort_key dictionary to logical column indexes."""
        if isinstance(sort_key, dict):
            default_val, resolved = self._normalize_scoped_dict(sort_key)
            result: dict[int | str, Any] = dict(resolved)
            if default_val is not None:
                result["default"] = default_val
            return result
        return sort_key

    def _re_normalize_scoped_attributes(self) -> None:
        """Re-normalize active scoped attribute dictionaries whenever headers change."""
        self._layout_mgr.reapply_show_columns_rules()
        self._set_editable_rules(self._raw_editable)
        self._header_controller.reapply_sortable_rules()
        self._update_colors()
        self._update_fonts()
        self._data_model.set_sort_key_rules(self._normalize_sort_key_for_model(self._raw_sort_key))

    @override
    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        self._update_colors()
        self._redraw()

    @override
    def _set_scaling(self, *args: Any, **kwargs: Any) -> None:
        super()._set_scaling(*args, **kwargs)
        self._update_fonts()
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
        border = int(self._border_width) if self._border_width else 0
        raw_spacing = self._border_spacing + border
        return scale(self, raw_spacing)

    def _re_grid_components(self) -> None:
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
        return scale(self, self._row_height)

    def _get_scaled_header_height(self) -> int:
        return scale(self, self._header_height)

    def _get_page_row_count(self) -> int:
        """Return how many whole rows fit in the visible body area, never less than one."""
        return max(1, self._table_canvas.winfo_height() // self._get_scaled_row_height())

    def _get_total_cols(self) -> int:
        if self._headers is not None:
            return len(self._headers)
        if hasattr(self, "_data_model") and self._data_model.row_count > 0 and self._data_model.values[0]:
            return len(self._data_model.values[0])
        return 0

    def _create_text_measure_lookup(self) -> TextMeasureLookup:
        """Build a lookup that returns the header and body text measuring functions for any column."""
        header_fallback = tkfont.Font(font=self._apply_font_scaling(self._get_base_header_font()))
        body_fallback = tkfont.Font(font=self._apply_font_scaling(self._get_base_font()))

        def lookup(col: int) -> tuple[Callable[[str], int], Callable[[str], int]]:
            """Return (header_measure, body_measure) for a column, using its own fonts when it has them."""
            header_font = self._cached_header_font_objs.get(col, header_fallback)
            body_font = self._cached_col_font_objs.get(col, body_fallback)
            return header_font.measure, body_font.measure

        return lookup

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
        _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
        max_scroll_x = self._get_max_scroll_x(col_offsets[-1])
        self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x + delta_pixels))
        self._redraw()

    def _on_mousewheel_v(self, event: Any) -> None:
        """Scroll the table up or down when the user turns the mouse wheel."""
        if self._data_model.row_count == 0:
            return
        scaled_row = self._get_scaled_row_height()
        delta = -int((event.delta / MOUSEWHEEL_BASE_DELTA) * scaled_row * MOUSEWHEEL_STEP_ROWS)
        self._scroll_y_by(delta)

    def _on_mousewheel_h(self, event: Any) -> None:
        """Scroll the table left or right when the user turns the mouse wheel with Shift held."""
        delta = -int((event.delta / MOUSEWHEEL_BASE_DELTA) * scale(self, HORIZONTAL_SCROLL_STEP_PX))
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
            delta = step_count * (scaled_row * MOUSEWHEEL_STEP_ROWS if unit == "units" else canvas_height)
            self._scroll_y_by(delta)

    def _on_h_scrollbar_command(self, action: str, *args: Any) -> None:
        """Handle clicks and drag actions from the horizontal scrollbar."""
        self._commit_edit()
        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
        total_width = col_offsets[-1]
        max_scroll_x = self._get_max_scroll_x(total_width)

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_x = max(0.0, min(max_scroll_x, fraction * total_width))
            self._redraw()
        elif action == "scroll" and len(args) >= 2:
            step_count = int(args[0])
            unit = args[1]
            delta = step_count * (scale(self, HORIZONTAL_SCROLL_STEP_PX) if unit == "units" else canvas_width)
            self._scroll_x_by(delta)

    def _on_canvas_configure(self, _event: Any) -> None:
        """Keep the view within safe bounds and resize the header whenever the window size changes."""
        canvas_width = self._table_canvas.winfo_width()
        _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
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
            visible_cols = self._layout_mgr.get_visible_columns()
            if col in visible_cols:
                _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
                target_v = visible_cols.index(col)
                target_x_left = col_offsets[target_v]
                target_x_right = col_offsets[target_v + 1]

                if target_x_left < self._scroll_x:
                    self._scroll_x = float(target_x_left)
                elif target_x_right > self._scroll_x + canvas_width:
                    self._scroll_x = float(target_x_right - canvas_width)

        self._redraw()

    # -------------------------------------------------------------------------
    # In-Place Editing Lifecycle
    # -------------------------------------------------------------------------

    def _set_editable_rules(self, editable: bool | dict[int | str, bool]) -> None:
        """Update editable state, preserving baseline when 'default' is omitted in incremental dict reconfigures."""
        self._raw_editable = editable
        if isinstance(editable, dict):
            default_val, resolved = self._normalize_scoped_dict(editable)
            if default_val is not None:
                self._editable_default = bool(default_val)
            for k, v in resolved.items():
                self._editable_cols[k] = bool(v)
        else:
            self._editable_default = bool(editable)
            self._editable_cols.clear()

    def _has_editable_cells(self) -> bool:
        """Check whether at least one column permits cell editing."""
        if self._editable_default:
            return True
        return any(self._editable_cols.values())

    def _is_column_editable(self, col: int) -> bool:
        """Check whether users are allowed to edit cells in this column."""
        if col in self._editable_cols:
            return self._editable_cols[col]
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

        x_left = col_offsets[v_idx] - self._scroll_x
        col_w = col_widths[v_idx]
        y_top = visual_row * scaled_row - self._scroll_y

        try:
            current_val = str(self._data_model.get_cell(visual_row, col))
        except IndexError:
            current_val = ""

        border_color_hex = self._cached_colors.get("selected_bg", self._resolve_color(self._selected_color))

        base_font = self._get_base_font()
        cell_font = self._resolve_font_descriptor(
            self._get_normalized_column_fonts().get(col, base_font),
            base_font,
        )
        cell_align = self._get_normalized_column_alignments().get(col, "left")

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
        visible_cols = self._layout_mgr.get_visible_columns()
        _, col_offsets = self._layout_mgr.calculate_geometry(canvas_width)
        scaled_row = self._get_scaled_row_height()

        row = int((pixel_y + self._scroll_y) // scaled_row)
        v_idx = bisect_right(col_offsets, pixel_x + self._scroll_x) - 1

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

        start_col = max(0, bisect_right(col_offsets, self._scroll_x) - 1 - self._overscan_cols)
        end_col = min(
            total_cols,
            bisect_left(col_offsets, self._scroll_x + canvas_w) + 1 + self._overscan_cols,
        )

        scaled_padding = scale(self, CELL_HORIZONTAL_PADDING)
        divider_hex = self._cached_colors.get("divider", self._resolve_color(self._divider_color))
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
            bg_hex=self._cached_colors.get("header_fg", self._resolve_color(self._header_fg_color)),
            text_color_hex=self._cached_colors.get("header_text", ""),
            divider_color_hex=divider_hex,
            header_font=self._apply_font_scaling(self._get_base_header_font()),
            sort_col=self._data_model.sort_column,
            sort_ascending=self._data_model.sort_ascending,
            scaled_padding=scaled_padding,
            header_alignments=self._get_normalized_header_alignments(),
            header_text_colors=self._cached_header_text_colors,
            header_fonts=self._cached_header_fonts,
            header_font_objs=self._cached_header_font_objs,
            hovered_col=self._header_controller.hovered_col,
            header_hover_color_hex=self._cached_colors.get("header_hover"),
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
            start_col = max(0, bisect_right(col_offsets, self._scroll_x) - 1 - self._overscan_cols)
            end_col = min(
                total_cols,
                bisect_left(col_offsets, self._scroll_x + canvas_w) + 1 + self._overscan_cols,
            )
        else:
            start_col, end_col = 0, 0

        scaled_padding = scale(self, CELL_HORIZONTAL_PADDING)
        divider_hex = self._cached_colors.get("divider", self._resolve_color(self._divider_color))

        # 1. Pinned Header Rendering
        if self._show_headers:
            self._redraw_header()

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
            text_color_hex=self._cached_colors.get("text", ""),
            selected_bg_hex=self._cached_colors.get("selected_bg", self._resolve_color(self._selected_color)),
            selected_text_hex=self._cached_colors.get("selected_text", self._resolve_color(self._selected_text_color)),
            row_even_bg=self._cached_colors.get("row_even", ""),
            row_odd_bg=self._cached_colors.get("row_odd", ""),
            divider_color_hex=divider_hex,
            body_font=self._apply_font_scaling(self._get_base_font()),
            scaled_padding=scaled_padding,
            column_alignments=self._get_normalized_column_alignments(),
            col_text_colors=self._cached_col_text_colors,
            col_fonts=self._cached_col_fonts,
            col_font_objs=self._cached_col_font_objs,
            visible_cols=visible_cols,
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
                raise IndexError(f"Column index {column} out of range [0, {total_cols})")
            return [self._data_model.get_cell(r, column) for r in range(self._data_model.row_count)]

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

    def update_cell(self, row_index: int, col_index: int, value: Any, notify: bool = True) -> None:
        """Update a specific cell value in-place, updating sorting if relevant."""
        old_val, storage_row = self._data_model.update_cell(row_index, col_index, value)

        if self._data_model.sort_column == col_index:
            self.sort_by(col_index, ascending=self._data_model.sort_ascending)
        else:
            self._redraw()

        if notify and self.on_cell_edit is not None:
            self.on_cell_edit(storage_row, col_index, old_val, value)

    def update_row(self, display_row: int, values: list[Any], notify: bool = True) -> None:
        """Update an entire row in-place, updating sorting if relevant."""
        if self._editor.is_editing and self._selection_manager.focused_row == display_row:
            self._cancel_edit()

        total_cols = self._get_total_cols()
        old_row, storage_row = self._data_model.update_row(display_row, values, total_cols=total_cols)

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
                    self.on_cell_edit(storage_row, c, old_row[c], values[c])

    def get_header(self, col_index: int) -> str:
        """Return the header title for a specific column index."""
        if self._headers is not None and 0 <= col_index < len(self._headers):
            return self._headers[col_index]
        return ""

    def set_header(self, col_index: int, title: str) -> None:
        """Set or update the title for a specific column header."""
        self.configure(headers={col_index: title})

    def insert_row(self, index: int | None = None, values: list[Any] | None = None) -> int:
        """Insert a row at display position index (or append if None). Return the new display index."""
        self._cancel_edit()
        total_cols = self._get_total_cols()
        visual_insert_pos, _ = self._data_model.insert_row(index, values, total_cols)

        self._selection_manager.adjust_indexes_after_insert(visual_insert_pos)

        if self._data_model.sort_column is not None:
            self.sort_by(self._data_model.sort_column, ascending=self._data_model.sort_ascending)
            # Re-locate the newly inserted row's visual slot after re-sorting
            storage_insert_pos = self._data_model.row_count - 1
            visual_insert_pos = self._data_model.get_display_row_index(storage_insert_pos)
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
            case "show_headers":
                return self._show_headers
            case "show_columns":
                return self._layout_mgr.show_columns_setting
            case "column_widths":
                return self._layout_mgr.column_widths
            case "sort_key":
                return self._data_model.sort_key
            case "header_sortable":
                return self._header_controller.sortable_setting
            case "editable":
                if not self._editable_cols:
                    return self._editable_default
                res: dict[int | str, bool] = dict(self._editable_cols)
                res["default"] = self._editable_default
                return res
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
            case "justify":
                return self._justify
            case "header_alignment":
                return self._header_alignment
            case "header_hover_color":
                return self._header_hover_color
            case "text_color":
                return self._text_color
            case "font":
                return self._font
            case "header_text_color":
                return self._header_text_color
            case "header_font":
                return self._header_font
            case _:
                return super().cget(attribute_name)

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Configure widget options dynamically and refresh the viewport in a single batched pass."""
        needs_redraw = require_redraw
        re_grid = False
        fonts_changed = False
        colors_changed = False

        if "values" in kwargs:
            new_values = kwargs.pop("values")
            self._commit_edit()
            self._data_model.reset_values(new_values)
            self._selection_manager.clear()
            self._scroll_y = 0.0
            needs_redraw = True

        if "headers" in kwargs:
            new_headers = kwargs.pop("headers")
            self._apply_headers(new_headers)
            if "show_headers" not in kwargs:
                self._show_headers = self._headers is not None
            self._re_normalize_scoped_attributes()
            re_grid = True
            needs_redraw = True

        if "show_headers" in kwargs:
            self._show_headers = bool(kwargs.pop("show_headers"))
            re_grid = True
            needs_redraw = True

        if "show_columns" in kwargs:
            self._layout_mgr.set_show_columns_rules(kwargs.pop("show_columns"))
            self._scroll_x = 0.0
            needs_redraw = True

        if "column_widths" in kwargs:
            self._layout_mgr.column_widths = kwargs.pop("column_widths")
            self._scroll_x = 0.0
            needs_redraw = True

        if "justify" in kwargs:
            self._justify = kwargs.pop("justify")
            needs_redraw = True

        if "header_alignment" in kwargs:
            self._header_alignment = kwargs.pop("header_alignment")
            needs_redraw = True

        if "header_hover_color" in kwargs:
            self._header_hover_color = kwargs.pop("header_hover_color")
            colors_changed = True
            needs_redraw = True

        if "editable" in kwargs:
            self._set_editable_rules(kwargs.pop("editable"))
            if not self._has_editable_cells():
                self._cancel_edit()

        if "header_sortable" in kwargs:
            self._header_controller.set_sortable_rules(kwargs.pop("header_sortable"))

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
            self._header_height = max(MIN_HEADER_HEIGHT, int(kwargs.pop("header_height")))
            needs_redraw = True

        if "border_spacing" in kwargs:
            self._border_spacing = max(0, int(kwargs.pop("border_spacing")))
            re_grid = True
            needs_redraw = True

        if "sort_key" in kwargs:
            sk = kwargs.pop("sort_key")
            self._raw_sort_key = sk
            self._data_model.set_sort_key_rules(self._normalize_sort_key_for_model(sk))
            needs_redraw = True

        if "on_cell_edit" in kwargs:
            self.on_cell_edit = kwargs.pop("on_cell_edit")

        if "command" in kwargs:
            self.command = kwargs.pop("command")

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
                ctk.ThemeManager.theme["CTkFrame"].get("top_fg_color", ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
                if h_fg is None
                else h_fg
            )
            colors_changed = True
            needs_redraw = True

        if "font" in kwargs:
            f_val = kwargs.pop("font")
            self._font = ctk.CTkFont() if f_val is None else f_val
            fonts_changed = True
            needs_redraw = True

        if "header_font" in kwargs:
            hf_val = kwargs.pop("header_font")
            self._header_font = ctk.CTkFont(weight="bold") if hf_val is None else hf_val
            fonts_changed = True
            needs_redraw = True

        if fonts_changed:
            self._update_fonts()

        if colors_changed:
            self._update_colors()

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
