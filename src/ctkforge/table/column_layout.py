"""Decides which table columns are visible, how wide each one is, and where each one starts.

Also snaps column widths to fit their content.
"""

from collections.abc import Callable
from typing import Any

from ctkforge.geometry import scale, unscale
from ctkforge.table.column_resizer import ColumnResizer
from ctkforge.table.constants import (
    AUTOFIT_FALLBACK_WIDTH,
    AUTOFIT_PADDING_PX,
    AUTOFIT_SAMPLE_ROWS,
    MIN_COLUMN_WIDTH,
)
from ctkforge.table.data_model import TableDataModel

__all__ = ["ColumnLayoutManager"]

type TextMeasure = Callable[[str], int]
type TextMeasureLookup = Callable[[int], tuple[TextMeasure, TextMeasure]]
type ScopedDictNormalizer = Callable[[dict[int | str, Any] | None], tuple[Any | None, dict[int, Any]]]


class ColumnLayoutManager:
    """Owns column visibility and width settings and turns them into pixel geometry."""

    def __init__(
        self,
        widget: Any,
        data_model: TableDataModel,
        *,
        show_columns: bool | dict[int | str, bool],
        column_widths: Any,
        get_total_cols: Callable[[], int],
        get_headers: Callable[[], list[str] | None],
        get_canvas_width: Callable[[], int],
        normalize_scoped_dict: ScopedDictNormalizer,
        resolve_col_index: Callable[[int | str], int | None],
        create_text_measure_lookup: Callable[[], TextMeasureLookup],
        on_layout_changed: Callable[[], None],
    ) -> None:
        """Wire the manager to the table through plain callbacks.

        Args:
            widget: The table widget, used only to read the DPI scaling factor.
            data_model: Source of row counts and cell text for auto-fit sampling.
            show_columns: Initial visibility rules (a single bool or a scoped dict).
            column_widths: Initial width rules (an int, "auto", or a scoped dict).
            get_total_cols: Returns how many logical columns the table has.
            get_headers: Returns the current header titles, or None when there are none.
            get_canvas_width: Returns the current body canvas width in pixels.
            normalize_scoped_dict: Splits a scoped dict into its default and per-column values.
            resolve_col_index: Turns an index or header title into a logical column index.
            create_text_measure_lookup: Builds a fresh per-column text measuring lookup.
            on_layout_changed: Called after widths change so the table can redraw.
        """
        self._widget = widget
        self._data_model = data_model
        self._get_total_cols = get_total_cols
        self._get_headers = get_headers
        self._get_canvas_width = get_canvas_width
        self._normalize_scoped_dict = normalize_scoped_dict
        self._resolve_col_index = resolve_col_index
        self._create_text_measure_lookup = create_text_measure_lookup
        self._on_layout_changed = on_layout_changed

        self._column_widths: Any = column_widths

        self._show_columns_default: bool = True
        self._show_columns_cols: dict[int, bool] = {}
        self._raw_show_columns: bool | dict[int | str, bool] = show_columns
        self.set_show_columns_rules(show_columns)

    # -------------------------------------------------------------------------
    # Column Visibility
    # -------------------------------------------------------------------------

    @property
    def show_columns_setting(self) -> bool | dict[int | str, bool]:
        """Return the visibility rules as a single bool, or a dict that includes a 'default' entry."""
        if not self._show_columns_cols:
            return self._show_columns_default
        result: dict[int | str, bool] = dict(self._show_columns_cols)
        result["default"] = self._show_columns_default
        return result

    def set_show_columns_rules(self, show_columns: bool | dict[int | str, bool]) -> None:
        """Apply new visibility rules, keeping the current baseline when a dict omits 'default'."""
        self._raw_show_columns = show_columns
        if isinstance(show_columns, dict):
            default_val, resolved = self._normalize_scoped_dict(show_columns)
            if default_val is not None:
                self._show_columns_default = bool(default_val)
            for col, is_shown in resolved.items():
                self._show_columns_cols[col] = bool(is_shown)
        else:
            self._show_columns_default = bool(show_columns)
            self._show_columns_cols.clear()

    def reapply_show_columns_rules(self) -> None:
        """Resolve the stored visibility rules again, so header title keys follow renamed headers."""
        self.set_show_columns_rules(self._raw_show_columns)

    def is_column_shown(self, col: int) -> bool:
        """Check whether a logical column is marked visible."""
        return self._show_columns_cols.get(col, self._show_columns_default)

    def get_visible_columns(self) -> list[int]:
        """Return the logical indexes of all visible columns, in order."""
        return [c for c in range(self._get_total_cols()) if self.is_column_shown(c)]

    # -------------------------------------------------------------------------
    # Column Widths & Geometry
    # -------------------------------------------------------------------------

    @property
    def column_widths(self) -> Any:
        """Return the width rules: an int, "auto", a scoped dict, or None."""
        return self._column_widths

    @column_widths.setter
    def column_widths(self, column_widths: Any) -> None:
        """Replace the width rules."""
        self._column_widths = column_widths

    def set_column_width(self, col: int, width_px: int) -> None:
        """Pin one column to a width given in on-screen pixels, leaving the other columns as they are."""
        self._ensure_explicit_widths()
        self._column_widths[col] = unscale(self._widget, width_px)

    def calculate_geometry(self, canvas_width: int) -> tuple[list[int], list[int]]:
        """Calculate each visible column's pixel width and its running start offsets.

        Returns:
            A pair of lists. The first holds one width per visible column. The second holds
            the start offset of each visible column, plus the total content width as its last item.
        """
        visible_cols = self.get_visible_columns()
        if not visible_cols:
            return [], [0]

        min_col_w = scale(self._widget, MIN_COLUMN_WIDTH)
        col_targets = self._resolve_width_targets(visible_cols)

        # Fixed columns take their scaled width; "auto" columns share whatever space is left
        fixed_widths: dict[int, int] = {}
        auto_positions: list[int] = []
        for position, target in enumerate(col_targets):
            if isinstance(target, int):
                fixed_widths[position] = max(min_col_w, scale(self._widget, target))
            else:
                auto_positions.append(position)

        slack = max(0, canvas_width - sum(fixed_widths.values()))
        auto_widths: dict[int, int] = {}
        if auto_positions:
            num_auto = len(auto_positions)
            base_auto = max(min_col_w, slack // num_auto)
            remainder = max(0, slack - (base_auto * num_auto))
            for i, position in enumerate(auto_positions):
                extra = 1 if i < remainder and (slack >= min_col_w * num_auto) else 0
                auto_widths[position] = base_auto + extra

        col_widths = [
            fixed_widths[position] if position in fixed_widths else auto_widths.get(position, min_col_w)
            for position in range(len(visible_cols))
        ]

        col_offsets = [0]
        cumulative = 0
        for width in col_widths:
            cumulative += width
            col_offsets.append(cumulative)

        return col_widths, col_offsets

    def _resolve_width_targets(self, visible_cols: list[int]) -> list[int | str]:
        """Pick a width target per visible column: a logical pixel width, or "auto" to share leftover space."""
        raw_widths = self._column_widths

        if raw_widths is None or (isinstance(raw_widths, str) and raw_widths.lower() == "auto"):
            return ["auto"] * len(visible_cols)

        if isinstance(raw_widths, (int, float)):
            return [max(MIN_COLUMN_WIDTH, int(raw_widths))] * len(visible_cols)

        if isinstance(raw_widths, dict):
            default_val, resolved = self._normalize_scoped_dict(raw_widths)
            fallback = default_val if default_val is not None else "auto"
            targets: list[int | str] = []
            for col in visible_cols:
                raw = resolved.get(col, fallback)
                if isinstance(raw, (int, float)):
                    targets.append(max(MIN_COLUMN_WIDTH, int(raw)))
                else:
                    targets.append("auto")
            return targets

        return ["auto"] * len(visible_cols)

    def _ensure_explicit_widths(self) -> None:
        """Freeze the current on-screen widths into a per-column dict so single columns can be changed."""
        if isinstance(self._column_widths, dict):
            return
        visible_cols = self.get_visible_columns()
        col_widths, _ = self.calculate_geometry(self._get_canvas_width())
        self._column_widths = {visible_cols[i]: unscale(self._widget, w) for i, w in enumerate(col_widths)}

    # -------------------------------------------------------------------------
    # Auto-Fit
    # -------------------------------------------------------------------------

    def auto_fit_columns(self, columns: list[int | str] | None = None) -> None:
        """Snap the given columns (or all visible ones) to fit their header and cell text, then redraw."""
        total_cols = self._get_total_cols()
        if total_cols == 0:
            return

        target_cols = self._resolve_auto_fit_targets(columns, total_cols)
        if not target_cols:
            return

        measure_lookup = self._create_text_measure_lookup()
        padding = scale(self._widget, AUTOFIT_PADDING_PX)
        sample_rows = min(AUTOFIT_SAMPLE_ROWS, self._data_model.row_count)
        headers = self._get_headers()

        # Freeze existing widths first so fitting one column never resets the others to "auto"
        self._ensure_explicit_widths()

        for col_index in target_cols:
            header_text = headers[col_index] if (headers and col_index < len(headers)) else None
            header_measure, body_measure = measure_lookup(col_index)
            fitted_width = ColumnResizer.calculate_autofit_width(
                header_text=header_text,
                sample_values=self._sample_column_text(col_index, sample_rows),
                header_measure=header_measure,
                body_measure=body_measure,
                padding=padding,
                fallback_width=AUTOFIT_FALLBACK_WIDTH,
            )
            self.set_column_width(col_index, fitted_width)

        self._on_layout_changed()

    def auto_fit_column(self, col_index: int | str) -> None:
        """Snap a single column to fit its header and cell text, leaving other columns untouched."""
        self.auto_fit_columns([col_index])

    def _resolve_auto_fit_targets(self, columns: list[int | str] | None, total_cols: int) -> list[int]:
        """Turn requested column keys into valid logical indexes, defaulting to every visible column."""
        if columns is None:
            return self.get_visible_columns()

        targets: list[int] = []
        for key in columns:
            index = self._resolve_col_index(key)
            if index is not None and 0 <= index < total_cols:
                targets.append(index)
        return targets

    def _sample_column_text(self, col_index: int, sample_rows: int) -> list[str]:
        """Read the text of the first few cells in a column for width measuring."""
        sample_values: list[str] = []
        for row in range(sample_rows):
            try:
                sample_values.append(str(self._data_model.get_cell(row, col_index)))
            except IndexError:
                continue
        return sample_values
