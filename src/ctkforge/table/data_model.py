"""Stores the tabular dataset, maps visible row indexes to storage rows, and handles column sorting.

This module provides the TableDataModel class, which holds table records in memory.
It separates visual display order from actual storage order, allowing fast sorting
without rearranging or mutating the original data list.
"""

from collections.abc import Callable
from typing import Any


class TableDataModel:
    """Manages tabular dataset storage, virtual row mappings, and type-aware sorting.

    Separates storage indexing from visual display indexing to allow instant
    in-place sorting without mutating underlying database records.
    """

    def __init__(
        self,
        values: list[list[Any]] | None = None,
        column_types: list[str] | dict[int, str] | None = None,
        column_sort_keys: dict[int, Callable[[Any], Any]] | None = None,
    ) -> None:
        self._values: list[list[Any]] = [list(row) for row in values] if values is not None else []
        self._row_indexes: list[int] = list(range(len(self._values)))
        self._column_types: list[str] | dict[int, str] | None = column_types
        self._column_sort_keys: dict[int, Callable[[Any], Any]] | None = column_sort_keys

        self._sort_col: int | None = None
        self._sort_ascending: bool = True

    @property
    def values(self) -> list[list[Any]]:
        """Return the underlying raw dataset."""
        return self._values

    @property
    def row_count(self) -> int:
        """Return the total number of records."""
        return len(self._values)

    @property
    def sort_column(self) -> int | None:
        """Return the active sorted column index, or None if unsorted."""
        return self._sort_col

    @property
    def sort_ascending(self) -> bool:
        """Return True if sorting ascending, False if descending."""
        return self._sort_ascending

    @property
    def column_types(self) -> list[str] | dict[int, str] | None:
        """Return the column type definitions."""
        return self._column_types

    @column_types.setter
    def column_types(self, types: list[str] | dict[int, str] | None) -> None:
        self._column_types = types

    @property
    def column_sort_keys(self) -> dict[int, Callable[[Any], Any]] | None:
        """Return custom sort key functions."""
        return self._column_sort_keys

    @column_sort_keys.setter
    def column_sort_keys(self, keys: dict[int, Callable[[Any], Any]] | None) -> None:
        self._column_sort_keys = keys

    def reset_values(self, new_values: list[list[Any]] | None) -> None:
        """Replace the dataset and reset virtual sorting state."""
        self._values = [list(row) for row in new_values] if new_values is not None else []
        self._row_indexes = list(range(len(self._values)))
        self._sort_col = None
        self._sort_ascending = True

    def get_raw_row_index(self, display_row: int) -> int:
        """Translate a visual display row index to its raw row index in memory."""
        if not (0 <= display_row < len(self._row_indexes)):
            raise IndexError(
                f"Display row index {display_row} out of range [0, {len(self._row_indexes)})"
            )
        return self._row_indexes[display_row]

    def get_display_row_index(self, raw_row: int) -> int:
        """Translate a raw row index to its current visual display index."""
        try:
            return self._row_indexes.index(raw_row)
        except ValueError as err:
            raise IndexError(
                f"Raw row index {raw_row} not found in active display mapping"
            ) from err

    def get_row(self, display_row: int) -> list[Any]:
        """Return a copy of the record at the specified display index."""
        raw_index = self.get_raw_row_index(display_row)
        return list(self._values[raw_index])

    def get_cell(self, display_row: int, col_index: int) -> Any:
        """Return the value of the cell at display row and column."""
        row_data = self.get_row(display_row)
        if not (0 <= col_index < len(row_data)):
            raise IndexError(
                f"Column index {col_index} out of range [0, {len(row_data)})"
            )
        return row_data[col_index]

    def get_all_rows(self) -> list[list[Any]]:
        """Return all rows arranged in their current visual display order."""
        return [list(self._values[storage_idx]) for storage_idx in self._row_indexes]

    def update_cell(self, display_row: int, col_index: int, value: Any) -> tuple[Any, int]:
        """Update a single cell value in storage.

        Returns:
            A tuple of (old_value, raw_row_index).
        """
        raw_idx = self.get_raw_row_index(display_row)
        row_data = self._values[raw_idx]

        while len(row_data) <= col_index:
            row_data.append("")

        old_value = row_data[col_index]
        row_data[col_index] = value
        return old_value, raw_idx

    def update_row(
        self, display_row: int, values: list[Any], total_cols: int | None = None
    ) -> tuple[list[Any], int]:
        """Update an entire row in storage at display_row.

        Args:
            display_row: Visual display row index.
            values: New column values for the row.
            total_cols: Optional minimum column count to pad missing columns with empty strings.

        Returns:
            A tuple of (old_row_values, raw_row_index).
        """
        raw_idx = self.get_raw_row_index(display_row)
        old_values = list(self._values[raw_idx])
        new_row = list(values)
        if total_cols is not None and len(new_row) < total_cols:
            new_row.extend([""] * (total_cols - len(new_row)))
        self._values[raw_idx] = new_row
        return old_values, raw_idx

    def insert_row(
        self,
        display_index: int | None,
        row_values: list[Any] | None,
        total_cols: int,
    ) -> tuple[int, int]:
        """Insert a row at the requested display index (or append if None).

        Returns:
            A tuple of (visual_insert_index, storage_insert_index).
        """
        if display_index is not None and self._sort_col is not None:
            self.commit_sort()

        if row_values is None:
            new_record = ["" for _ in range(total_cols)]
        else:
            new_record = list(row_values)
            if len(new_record) < total_cols:
                new_record.extend([""] * (total_cols - len(new_record)))

        storage_insert_pos = len(self._values)
        self._values.append(new_record)

        if display_index is None or display_index >= len(self._row_indexes):
            visual_insert_pos = len(self._row_indexes)
            self._row_indexes.append(storage_insert_pos)
        else:
            visual_insert_pos = max(0, display_index)
            self._row_indexes.insert(visual_insert_pos, storage_insert_pos)

        return visual_insert_pos, storage_insert_pos

    def delete_rows(self, display_indexes: list[int] | set[int] | int) -> set[int]:
        """Delete records by display index using a linear single-pass index reconstruction.

        Returns:
            Set of valid display row indexes that were deleted.
        """
        if isinstance(display_indexes, int):
            targets = {display_indexes}
        else:
            targets = set(display_indexes)

        valid_targets = {idx for idx in targets if 0 <= idx < len(self._row_indexes)}
        if not valid_targets:
            return set()

        storage_to_delete = {self._row_indexes[idx] for idx in valid_targets}

        kept_values: list[list[Any]] = []
        old_to_new_storage_map: dict[int, int] = {}
        new_storage_idx = 0

        for old_idx, row_data in enumerate(self._values):
            if old_idx not in storage_to_delete:
                kept_values.append(row_data)
                old_to_new_storage_map[old_idx] = new_storage_idx
                new_storage_idx += 1

        self._values = kept_values

        new_row_indexes: list[int] = []
        for display_idx, old_storage in enumerate(self._row_indexes):
            if display_idx not in valid_targets:
                new_row_indexes.append(old_to_new_storage_map[old_storage])

        self._row_indexes = new_row_indexes
        return valid_targets

    def extract_sort_value(self, raw_val: Any, col: int) -> Any:
        """Convert a cell value into a normalized, comparable sort key without crashing."""
        if self._column_sort_keys and col in self._column_sort_keys:
            try:
                return self._column_sort_keys[col](raw_val)
            except (ValueError, TypeError, KeyError, AttributeError):
                return str(raw_val).lower()

        col_type = None
        if (
            (isinstance(self._column_types, list) and col < len(self._column_types))
            or (isinstance(self._column_types, dict) and col in self._column_types)
        ):
            col_type = self._column_types[col]

        if col_type == "int":
            try:
                return int(raw_val)
            except (ValueError, TypeError):
                cleaned = "".join(ch for ch in str(raw_val) if ch.isdigit() or ch == "-")
                try:
                    return int(cleaned) if cleaned and cleaned != "-" else 0
                except ValueError:
                    return 0

        if col_type == "float":
            try:
                return float(raw_val)
            except (ValueError, TypeError):
                cleaned = "".join(ch for ch in str(raw_val) if ch.isdigit() or ch in ".-")
                try:
                    return float(cleaned) if cleaned and cleaned not in (".", "-", ".-") else 0.0
                except ValueError:
                    return 0.0

        if col_type == "date":
            return str(raw_val)

        return str(raw_val).lower()

    def sort_by(self, column_index: int, ascending: bool = True) -> None:
        """Sort rows via index indirection without mutating raw dataset storage."""
        if not self._values:
            return

        self._row_indexes.sort(
            key=lambda idx: self.extract_sort_value(
                self._values[idx][column_index] if column_index < len(self._values[idx]) else "",
                column_index,
            ),
            reverse=not ascending,
        )
        self._sort_col = column_index
        self._sort_ascending = ascending

    def clear_sort(self) -> None:
        """Restore initial unsorted display order."""
        self._row_indexes = list(range(len(self._values)))
        self._sort_col = None
        self._sort_ascending = True

    def commit_sort(self) -> None:
        """Permanently bake current visual sorted order into storage and reset sort flags."""
        if self._sort_col is None:
            return
        self._values = [self._values[i] for i in self._row_indexes]
        self._row_indexes = list(range(len(self._values)))
        self._sort_col = None
        self._sort_ascending = True
