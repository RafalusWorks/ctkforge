"""Calculates cell and row selections from clicks, tracks keyboard navigation, and exports text for copying.

Handles single, multiple, and range selections using mouse clicks and arrow keys.
Formats selected cells into tab-separated text ready for the clipboard.
"""

from collections.abc import Callable
from typing import Any, Literal

from ctkforge.table.data_model import TableDataModel


class SelectionManager:
    """Manages active cell and row selections, keyboard focus anchors, and TSV export."""

    def __init__(
        self,
        target: Literal["row", "cell"] = "row",
        mode: Literal["single", "extended", "none"] = "single",
    ) -> None:
        """Initialize selection state, target mode, and focus tracking."""
        self._selected_rows: set[int] = set()
        self._selected_cells: set[tuple[int, int]] = set()

        self._focused_row: int | None = None
        self._focused_col: int | None = None
        self._anchor_row: int | None = None
        self._anchor_col: int | None = None

        self.set_target(target)
        self.set_mode(mode)

    @property
    def target(self) -> Literal["row", "cell"]:
        """Return active selection target ('row' or 'cell')."""
        return self._target

    def set_target(self, target: Literal["row", "cell"]) -> None:
        """Set whether selections highlight entire rows or individual cells ('row' or 'cell')."""
        if target not in ("row", "cell"):
            raise ValueError(f"Invalid selection_target '{target}'; expected 'row' or 'cell'")
        self._target: Literal["row", "cell"] = target
        self.clear()

    @property
    def mode(self) -> Literal["single", "extended", "none"]:
        """Return active selection mode ('single', 'extended', 'none')."""
        return self._mode

    def set_mode(self, mode: Literal["single", "extended", "none"]) -> None:
        """Set selection behavior mode ('single', 'extended', or 'none')."""
        if mode not in ("single", "extended", "none"):
            raise ValueError(f"Invalid selection_mode '{mode}'; expected 'single', 'extended', or 'none'")
        self._mode: Literal["single", "extended", "none"] = mode
        if mode == "none":
            self.clear()
        elif mode == "single" and len(self._selected_rows) > 1:
            first_row = next(iter(self._selected_rows))
            self._selected_rows = {first_row}

    @property
    def selected_rows(self) -> set[int]:
        """Return current set of selected display row indexes."""
        return self._selected_rows

    @property
    def selected_cells(self) -> set[tuple[int, int]]:
        """Return current set of selected (row, column) tuples."""
        return self._selected_cells

    @property
    def focused_row(self) -> int | None:
        """Return the current display row holding keyboard focus."""
        return self._focused_row

    @focused_row.setter
    def focused_row(self, row: int | None) -> None:
        """Set the current display row holding keyboard focus."""
        self._focused_row = row

    @property
    def focused_col(self) -> int | None:
        """Return the current column index holding keyboard focus."""
        return self._focused_col

    @focused_col.setter
    def focused_col(self, col: int | None) -> None:
        """Set the current column index holding keyboard focus."""
        self._focused_col = col

    def clear(self) -> None:
        """Clear all highlighted rows, cells, and keyboard focus outlines."""
        self._selected_rows.clear()
        self._selected_cells.clear()
        self._focused_row = None
        self._focused_col = None
        self._anchor_row = None
        self._anchor_col = None

    def apply_click(
        self,
        row: int,
        col: int,
        is_ctrl: bool = False,
        is_shift: bool = False,
    ) -> None:
        """Update selections and keyboard focus when a cell or row is clicked."""
        if self._mode == "none":
            return

        self._focused_row = row
        self._focused_col = col

        if self._target == "row":
            self._apply_row_click(row, is_ctrl=is_ctrl, is_shift=is_shift)
        else:
            self._apply_cell_click(row, col, is_ctrl=is_ctrl, is_shift=is_shift)

    def _apply_row_click(self, row: int, is_ctrl: bool, is_shift: bool) -> None:
        """Handle row selection changes for normal clicks, Ctrl toggles, or Shift ranges."""
        if self._mode == "single" or not (is_ctrl or is_shift):
            self._selected_rows = {row}
            self._anchor_row = row
            return

        if self._mode == "extended":
            if is_ctrl:
                if row in self._selected_rows:
                    self._selected_rows.remove(row)
                else:
                    self._selected_rows.add(row)
                self._anchor_row = row
            elif is_shift and self._anchor_row is not None:
                start_row = min(self._anchor_row, row)
                end_row = max(self._anchor_row, row)
                self._selected_rows = set(range(start_row, end_row + 1))

    def _apply_cell_click(self, row: int, col: int, is_ctrl: bool, is_shift: bool) -> None:
        """Handle cell selection changes for normal clicks, Ctrl toggles, or Shift bounding boxes."""
        cell = (row, col)
        if self._mode == "single" or not (is_ctrl or is_shift):
            self._selected_cells = {cell}
            self._anchor_row = row
            self._anchor_col = col
            return

        if self._mode == "extended":
            if is_ctrl:
                if cell in self._selected_cells:
                    self._selected_cells.remove(cell)
                else:
                    self._selected_cells.add(cell)
                self._anchor_row = row
                self._anchor_col = col
            elif is_shift and self._anchor_row is not None and self._anchor_col is not None:
                r_low = min(self._anchor_row, row)
                r_high = max(self._anchor_row, row)
                c_low = min(self._anchor_col, col)
                c_high = max(self._anchor_col, col)

                cells: set[tuple[int, int]] = set()
                for r in range(r_low, r_high + 1):
                    for c in range(c_low, c_high + 1):
                        cells.add((r, c))
                self._selected_cells = cells

    def navigate(
        self,
        delta_row: int,
        delta_col: int,
        total_rows: int,
        total_cols: int,
        is_shift: bool = False,
    ) -> tuple[int, int]:
        """Move keyboard focus by row/column offset and update selection if Shift is held."""
        if total_rows == 0 or total_cols == 0:
            return 0, 0

        if self._focused_row is None:
            new_r = 0
            new_c = 0
        else:
            new_r = max(0, min(total_rows - 1, self._focused_row + delta_row))
            cur_c = self._focused_col if self._focused_col is not None else 0
            new_c = max(0, min(total_cols - 1, cur_c + delta_col))

        use_shift = is_shift and self._mode == "extended"
        self.apply_click(new_r, new_c, is_ctrl=False, is_shift=use_shift)
        return new_r, new_c

    def select_all(self, total_rows: int, total_cols: int) -> None:
        """Select all visible rows or cells if extended selection is permitted."""
        if self._mode != "extended":
            return

        if self._target == "row":
            self._selected_rows = set(range(total_rows))
        else:
            all_cells: set[tuple[int, int]] = set()
            for r in range(total_rows):
                for c in range(total_cols):
                    all_cells.add((r, c))
            self._selected_cells = all_cells

    def select_row(self, row_index: int, total_rows: int) -> None:
        """Select a single row by its visual row index."""
        if not (0 <= row_index < total_rows):
            raise IndexError(f"Row index {row_index} out of range [0, {total_rows})")

        if self._mode == "none":
            return
        if self._mode == "single":
            self._selected_rows = {row_index}
        else:
            self._selected_rows.add(row_index)
        self._focused_row = row_index

    def deselect_row(self, row_index: int) -> None:
        """Remove a row from the current selection."""
        self._selected_rows.discard(row_index)

    def select_cell(self, row_index: int, col_index: int, total_rows: int, total_cols: int) -> None:
        """Select a single cell by its row and column coordinates."""
        if not (0 <= row_index < total_rows):
            raise IndexError(f"Row index {row_index} out of range [0, {total_rows})")
        if not (0 <= col_index < total_cols):
            raise IndexError(f"Column index {col_index} out of range [0, {total_cols})")

        if self._mode == "none":
            return
        cell = (row_index, col_index)
        if self._mode == "single":
            self._selected_cells = {cell}
        else:
            self._selected_cells.add(cell)
        self._focused_row = row_index
        self._focused_col = col_index

    def adjust_indexes_after_insert(self, insert_display_pos: int) -> None:
        """Shift selected row and cell positions down when a new row is inserted."""
        if self._selected_rows:
            self._selected_rows = {r + 1 if r >= insert_display_pos else r for r in self._selected_rows}
        if self._selected_cells:
            self._selected_cells = {(r + 1, c) if r >= insert_display_pos else (r, c) for r, c in self._selected_cells}
        if self._focused_row is not None and self._focused_row >= insert_display_pos:
            self._focused_row += 1
        if self._anchor_row is not None and self._anchor_row >= insert_display_pos:
            self._anchor_row += 1

    def adjust_indexes_after_delete(self, deleted_display_targets: set[int], new_total_rows: int) -> None:
        """Shift selected row and cell positions up after rows are deleted."""
        self._selected_rows.difference_update(deleted_display_targets)

        # Build clean index mapping in a single pass instead of looping set rebuilds
        new_row_map: dict[int, int] = {}
        offset = 0
        max_idx = max(max(deleted_display_targets, default=0), new_total_rows + len(deleted_display_targets))
        for old_idx in range(max_idx + 1):
            if old_idx in deleted_display_targets:
                offset += 1
            else:
                new_row_map[old_idx] = old_idx - offset

        self._selected_rows = {new_row_map[r] for r in self._selected_rows if r in new_row_map}

        new_cells: set[tuple[int, int]] = set()
        for r, c in self._selected_cells:
            if r not in deleted_display_targets and r in new_row_map:
                new_cells.add((new_row_map[r], c))
        self._selected_cells = new_cells

        if self._focused_row is not None:
            if self._focused_row in deleted_display_targets:
                self._focused_row = min(self._focused_row, new_total_rows - 1) if new_total_rows > 0 else None
            elif self._focused_row in new_row_map:
                self._focused_row = new_row_map[self._focused_row]

        if self._anchor_row is not None:
            if self._anchor_row in deleted_display_targets:
                self._anchor_row = min(self._anchor_row, new_total_rows - 1) if new_total_rows > 0 else None
            elif self._anchor_row in new_row_map:
                self._anchor_row = new_row_map[self._anchor_row]

    def export_tsv(
        self,
        data_model: TableDataModel,
        format_cell: Callable[[int, Any], str] | None = None,
    ) -> str:
        """Format selected rows or cells as tab-separated text for the clipboard."""
        lines: list[str] = []

        def _format(c: int, val: Any) -> str:
            if format_cell is not None:
                return format_cell(c, val)
            return str(val)

        if self._target == "row" and self._selected_rows:
            for display_row in sorted(self._selected_rows):
                if display_row < data_model.row_count:
                    record = data_model.get_row(display_row)
                    lines.append("\t".join(_format(c, cell) for c, cell in enumerate(record)))
        elif self._selected_cells:
            grouped: dict[int, list[tuple[int, Any]]] = {}
            for display_row, col_idx in self._selected_cells:
                if display_row < data_model.row_count:
                    try:
                        val = data_model.get_cell(display_row, col_idx)
                    except IndexError:
                        val = ""
                    grouped.setdefault(display_row, []).append((col_idx, val))

            for display_row in sorted(grouped.keys()):
                cells = sorted(grouped[display_row], key=lambda x: x[0])
                lines.append("\t".join(_format(col_idx, val) for col_idx, val in cells))
        elif (
            self._focused_row is not None and self._focused_col is not None and self._focused_row < data_model.row_count
        ):
            try:
                lines.append(_format(self._focused_col, data_model.get_cell(self._focused_row, self._focused_col)))
            except IndexError:
                pass

        return "\n".join(lines)
