"""Works out the colors, fonts, and text alignment the table draws with.

Holds the raw style settings, turns theme color pairs into plain hex colors, scales fonts for the
screen, and understands settings that target single columns by index or header title.
"""

import tkinter.font as tkfont
from collections.abc import Callable, Mapping
from typing import Any, Final

import customtkinter as ctk

from ctkforge.table.column_layout import TextMeasureLookup

__all__ = ["ALIGNMENT_OPTIONS", "COLOR_OPTIONS", "FONT_OPTIONS", "STYLE_OPTIONS", "StyleResolver"]

COLOR_OPTIONS: Final = frozenset(
    {
        "text_color",
        "header_text_color",
        "selected_color",
        "selected_text_color",
        "header_fg_color",
        "row_color",
        "alternate_row_color",
        "header_hover_color",
    }
)
FONT_OPTIONS: Final = frozenset({"font", "header_font"})
ALIGNMENT_OPTIONS: Final = frozenset({"justify", "header_alignment"})
STYLE_OPTIONS: Final = COLOR_OPTIONS | FONT_OPTIONS | ALIGNMENT_OPTIONS

_VALID_ALIGNMENTS: Final = ("left", "center", "right")
_FONT_SHORTCUTS: Final = ("bold", "italic", "bold italic", "bold_italic")


class StyleResolver:
    """Owns the table's style settings and keeps ready-to-draw colors and fonts up to date."""

    def __init__(
        self,
        *,
        options: Mapping[str, Any],
        divider_color: str | tuple[str, str] | list[str],
        get_headers: Callable[[], list[str] | None],
        get_total_cols: Callable[[], int],
        get_frame_color: Callable[[], Any],
        apply_font_scaling: Callable[[Any], Any],
    ) -> None:
        """Store the initial style settings and build the first set of colors and fonts.

        Args:
            options: Initial values for every name in STYLE_OPTIONS. A None value means "use the theme default".
            divider_color: Color of the lines between columns.
            get_headers: Returns the current header titles, or None when there are none.
            get_total_cols: Returns how many logical columns the table has.
            get_frame_color: Returns the table frame's own background color.
            apply_font_scaling: Scales a font for the current screen DPI.
        """
        self._divider_color = divider_color
        self._get_headers = get_headers
        self._get_total_cols = get_total_cols
        self._get_frame_color = get_frame_color
        self._apply_font_scaling = apply_font_scaling

        self._options: dict[str, Any] = {
            name: self._with_theme_default(name, options.get(name)) for name in STYLE_OPTIONS
        }

        self._colors: dict[str, str] = {}
        self._column_text_colors: dict[int, str] = {}
        self._header_text_colors: dict[int, str] = {}
        self._column_fonts: dict[int, Any] = {}
        self._column_font_objs: dict[int, tkfont.Font] = {}
        self._header_fonts: dict[int, Any] = {}
        self._header_font_objs: dict[int, tkfont.Font] = {}

        self.update_colors()
        self.update_fonts()

    # -------------------------------------------------------------------------
    # Style Settings
    # -------------------------------------------------------------------------

    def get_option(self, name: str) -> Any:
        """Return the current value of a style setting, such as 'font' or 'row_color'."""
        return self._options[name]

    def configure_options(self, options: Mapping[str, Any]) -> None:
        """Apply new style settings and refresh the ready-to-draw colors and fonts they affect."""
        for name, value in options.items():
            self._options[name] = self._with_theme_default(name, value)

        if options.keys() & COLOR_OPTIONS:
            self.update_colors()
        if options.keys() & FONT_OPTIONS:
            self.update_fonts()

    @property
    def has_header_hover_color(self) -> bool:
        """Return whether a header hover highlight color is set."""
        return self._options["header_hover_color"] is not None

    @staticmethod
    def _with_theme_default(name: str, value: Any) -> Any:
        """Swap a missing (None) value for the theme default, for settings that have one."""
        if value is not None:
            return value

        theme = ctk.ThemeManager.theme
        defaults: dict[str, Callable[[], Any]] = {
            "font": ctk.CTkFont,
            "header_font": lambda: ctk.CTkFont(weight="bold"),
            "text_color": lambda: theme["CTkLabel"]["text_color"],
            "header_text_color": lambda: theme["CTkLabel"]["text_color"],
            "selected_color": lambda: theme["CTkButton"]["fg_color"],
            "selected_text_color": lambda: theme["CTkButton"]["text_color"],
            "header_fg_color": lambda: theme["CTkFrame"].get("top_fg_color", theme["CTkFrame"]["fg_color"]),
        }
        factory = defaults.get(name)
        return factory() if factory is not None else None

    # -------------------------------------------------------------------------
    # Column Scoping
    # -------------------------------------------------------------------------

    def resolve_col_index(self, key: int | str) -> int | None:
        """Turn an index or a header title into a logical column index, or None when it matches nothing."""
        if isinstance(key, int):
            return key
        if str(key).lower() == "default":
            return None
        try:
            return int(key)
        except (ValueError, TypeError):
            headers = self._get_headers()
            if headers is not None and key in headers:
                return headers.index(key)
            return None

    def normalize_scoped_dict[T](
        self,
        mapping: dict[int | str, T] | None,
    ) -> tuple[T | None, dict[int, T]]:
        """Split a per-column settings dict into its 'default' value and a {column_index: value} dict."""
        if not isinstance(mapping, dict):
            return None, {}

        default_val: T | None = None
        resolved: dict[int, T] = {}

        for raw_key, value in mapping.items():
            if str(raw_key).lower() == "default":
                default_val = value
                continue

            index = self.resolve_col_index(raw_key)
            if index is not None:
                resolved[index] = value

        return default_val, resolved

    # -------------------------------------------------------------------------
    # Colors
    # -------------------------------------------------------------------------

    @property
    def colors(self) -> dict[str, str]:
        """Return the ready-to-draw hex colors, keyed by role such as 'divider' or 'selected_bg'."""
        return self._colors

    @property
    def column_text_colors(self) -> dict[int, str]:
        """Return hex text colors for columns that have their own color."""
        return self._column_text_colors

    @property
    def header_text_colors(self) -> dict[int, str]:
        """Return hex header text colors for columns that have their own color."""
        return self._header_text_colors

    def resolve_color(self, color: Any) -> str:
        """Turn a theme color (single color or light/dark pair) into a plain hex string for the Tk canvas."""
        if color is None:
            return ""
        if isinstance(color, dict):
            return self.resolve_color(color.get("default", ""))
        if isinstance(color, (tuple, list)):
            return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]
        return str(color)

    def get_canvas_background(self) -> str:
        """Return the hex color the canvases should use as their background."""
        canvas_bg = self.resolve_color(self._get_frame_color())
        if not canvas_bg or canvas_bg == "transparent":
            canvas_bg = self.resolve_color(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        return canvas_bg

    def get_column_text_colors(self) -> dict[int, Any]:
        """Return the raw text color set for each column that has its own, by column index."""
        return self._get_scoped_values("text_color")

    def update_colors(self) -> None:
        """Rebuild the ready-to-draw hex colors from the current settings and appearance mode."""
        opts = self._options
        base_color = opts["row_color"] if opts["row_color"] is not None else self._get_frame_color()
        alt_color = opts["alternate_row_color"] if opts["alternate_row_color"] is not None else base_color

        self._colors = {
            "header_fg": self.resolve_color(opts["header_fg_color"]),
            "header_text": self.resolve_color(self._get_default_value("header_text_color")),
            "divider": self.resolve_color(self._divider_color),
            "text": self.resolve_color(self._get_default_value("text_color")),
            "selected_bg": self.resolve_color(opts["selected_color"]),
            "selected_text": self.resolve_color(opts["selected_text_color"]),
            "row_even": self.resolve_color(base_color),
            "row_odd": self.resolve_color(alt_color),
        }
        if opts["header_hover_color"] is not None:
            self._colors["header_hover"] = self.resolve_color(opts["header_hover_color"])

        self._column_text_colors = {c: self.resolve_color(v) for c, v in self._get_scoped_values("text_color").items()}
        self._header_text_colors = {
            c: self.resolve_color(v) for c, v in self._get_scoped_values("header_text_color").items()
        }

    # -------------------------------------------------------------------------
    # Fonts
    # -------------------------------------------------------------------------

    @property
    def column_fonts(self) -> dict[int, Any]:
        """Return scaled fonts for columns that have their own font."""
        return self._column_fonts

    @property
    def column_font_objs(self) -> dict[int, tkfont.Font]:
        """Return measuring font objects for columns that have their own font."""
        return self._column_font_objs

    @property
    def header_fonts(self) -> dict[int, Any]:
        """Return scaled header fonts for columns that have their own header font."""
        return self._header_fonts

    @property
    def header_font_objs(self) -> dict[int, tkfont.Font]:
        """Return measuring font objects for columns that have their own header font."""
        return self._header_font_objs

    def get_scaled_body_font(self) -> Any:
        """Return the default body font, scaled for the current screen."""
        return self._apply_font_scaling(self._get_base_font("font", ctk.CTkFont))

    def get_scaled_header_font(self) -> Any:
        """Return the default header font, scaled for the current screen."""
        return self._apply_font_scaling(self._get_base_font("header_font", lambda: ctk.CTkFont(weight="bold")))

    def get_column_font(self, col: int) -> Any:
        """Return the unscaled font a column's cells use, for the cell editor to match."""
        base_font = self._get_base_font("font", ctk.CTkFont)
        return self._resolve_font_descriptor(self._get_scoped_values("font").get(col, base_font), base_font)

    def update_fonts(self) -> None:
        """Rebuild the scaled fonts and measuring font objects for every column that has its own font."""
        base_body = self._get_base_font("font", ctk.CTkFont)
        base_header = self._get_base_font("header_font", lambda: ctk.CTkFont(weight="bold"))

        self._column_fonts, self._column_font_objs = self._build_scaled_fonts(
            self._get_scoped_values("font"), base_body
        )
        self._header_fonts, self._header_font_objs = self._build_scaled_fonts(
            self._get_scoped_values("header_font"), base_header
        )

    def create_text_measure_lookup(self) -> TextMeasureLookup:
        """Build a lookup that returns the header and body text measuring functions for any column."""
        header_fallback = tkfont.Font(font=self.get_scaled_header_font())
        body_fallback = tkfont.Font(font=self.get_scaled_body_font())

        def lookup(col: int) -> tuple[Callable[[str], int], Callable[[str], int]]:
            """Return (header_measure, body_measure) for a column, using its own fonts when it has them."""
            header_font = self._header_font_objs.get(col, header_fallback)
            body_font = self._column_font_objs.get(col, body_fallback)
            return header_font.measure, body_font.measure

        return lookup

    def _build_scaled_fonts(
        self,
        raw_fonts: dict[int, Any],
        base_font: tuple[str, int] | ctk.CTkFont,
    ) -> tuple[dict[int, Any], dict[int, tkfont.Font]]:
        """Resolve each column's font and return its scaled version plus a font object for measuring text."""
        scaled_fonts: dict[int, Any] = {}
        font_objs: dict[int, tkfont.Font] = {}
        for col, raw_font in raw_fonts.items():
            scaled = self._apply_font_scaling(self._resolve_font_descriptor(raw_font, base_font))
            scaled_fonts[col] = scaled
            font_objs[col] = tkfont.Font(font=scaled)
        return scaled_fonts, font_objs

    @staticmethod
    def _resolve_font_descriptor(raw_font: Any, base_font: tuple[str, int] | ctk.CTkFont) -> Any:
        """Turn a font shortcut ('bold', 'italic', 'bold italic') into a real font based on the default one."""
        if not isinstance(raw_font, str):
            return raw_font

        shortcut = raw_font.lower().strip()
        if shortcut not in _FONT_SHORTCUTS:
            return raw_font

        family = "TkDefaultFont"
        size = 13
        if isinstance(base_font, ctk.CTkFont):
            family = base_font.cget("family")
            size = base_font.cget("size")
        elif isinstance(base_font, (tuple, list)) and len(base_font) >= 2:
            family = str(base_font[0])
            size = int(base_font[1])

        return ctk.CTkFont(
            family=family,
            size=size,
            weight="bold" if "bold" in shortcut else "normal",
            slant="italic" if "italic" in shortcut else "roman",
        )

    def _get_base_font(self, option: str, fallback: Callable[[], ctk.CTkFont]) -> tuple[str, int] | ctk.CTkFont:
        """Return the default font for a font setting, whether it was given directly or as a dict's 'default'."""
        value = self._options[option]
        if isinstance(value, dict) and "default" in value:
            return value["default"]
        if isinstance(value, (ctk.CTkFont, tuple)):
            return value
        return fallback()

    # -------------------------------------------------------------------------
    # Alignment
    # -------------------------------------------------------------------------

    def get_column_alignments(self) -> dict[int, str]:
        """Return the text alignment ('left', 'center', 'right') of each column that has one, by column index."""
        return self._get_alignments("justify")

    def get_header_alignments(self) -> dict[int, str]:
        """Return the header text alignment of each column that has one, by column index."""
        return self._get_alignments("header_alignment")

    def _get_alignments(self, option: str) -> dict[int, str]:
        """Expand an alignment setting (single value or per-column dict) into one alignment per column."""
        total_cols = self._get_total_cols()
        value = self._options[option]

        if isinstance(value, str):
            align = value.lower()
            return {c: align for c in range(total_cols)} if align in _VALID_ALIGNMENTS else {}

        if isinstance(value, dict):
            default_val, resolved = self.normalize_scoped_dict(value)
            alignments: dict[int, str] = {}
            if default_val is not None and str(default_val).lower() in _VALID_ALIGNMENTS:
                alignments = {c: str(default_val).lower() for c in range(total_cols)}
            for col, align in resolved.items():
                if isinstance(align, str) and align.lower() in _VALID_ALIGNMENTS:
                    alignments[col] = align.lower()
            return alignments

        return {}

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _get_scoped_values(self, option: str) -> dict[int, Any]:
        """Return the per-column entries of a setting that may be a per-column dict, by column index."""
        value = self._options[option]
        if isinstance(value, dict):
            _, resolved = self.normalize_scoped_dict(value)
            return resolved
        return {}

    def _get_default_value(self, option: str) -> Any:
        """Return the setting's value for columns without their own entry (the dict's 'default' if it is one)."""
        value = self._options[option]
        if isinstance(value, dict):
            return value.get("default", ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        return value
