"""Stores the tabular dataset, maps visible row indexes to storage rows, and handles column sorting.

Holds table records in memory and separates visual display order from actual storage
order, allowing fast sorting without rearranging or mutating the original data list.
"""

from collections.abc import Callable
from typing import Any, Literal

SortKey = Literal["str", "int", "float", "date"] | Callable[[Any], Any]

__all__ = ["SortKey", "TableDataModel"]


class TableDataModel:
    """Manages tabular dataset storage, virtual row mappings, and type-aware sorting.

    Separates storage indexing from visual display indexing to allow instant
    in-place sorting without mutating underlying database records.
    """

    def __init__(
        self,
        values: list[list[Any]] | None = None,
        sort_key: SortKey | dict[int | str, SortKey] | None = None,
    ) -> None:
        """Initialize dataset storage, visual row mappings, and sort key rules."""
        self._values: list[list[Any]] = [list(row) for row in values] if values is not None else []
        self._row_ids: list[int] = list(range(len(self._values)))
        self._next_row_id: int = len(self._values)
        self._row_indexes: list[int] = list(range(len(self._values)))
        self._sort_key_default: SortKey = "str"
        self._sort_key_cols: dict[int, SortKey] = {}
        self.set_sort_key_rules(sort_key)

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
    def sort_key(self) -> dict[str | int, SortKey]:
        """Return the active sort key configuration."""
        res: dict[str | int, SortKey] = {"default": self._sort_key_default}
        res.update(self._sort_key_cols)
        return res

    def set_sort_key_rules(self, rules: SortKey | dict[int | str, SortKey] | None) -> None:
        """Update column sorting rules while preserving the active baseline when 'default' is omitted."""
        if rules is None:
            return
        valid_keys = {"str", "int", "float", "date"}
        if callable(rules):
            self._sort_key_default = rules
            self._sort_key_cols.clear()
            return
        if isinstance(rules, str):
            key = rules.lower()
            if key in valid_keys:
                self._sort_key_default = key  # type: ignore[assignment]
                self._sort_key_cols.clear()
            return
        if isinstance(rules, dict):
            if "default" in rules:
                val = rules["default"]
                if callable(val):
                    self._sort_key_default = val
                elif isinstance(val, str) and val.lower() in valid_keys:
                    self._sort_key_default = val.lower()  # type: ignore[assignment]
            for col_idx, key_val in rules.items():
                if str(col_idx).lower() == "default":
                    continue
                try:
                    c = int(col_idx)
                    if callable(key_val):
                        self._sort_key_cols[c] = key_val
                    elif isinstance(key_val, str) and key_val.lower() in valid_keys:
                        self._sort_key_cols[c] = key_val.lower()  # type: ignore[assignment]
                except (ValueError, TypeError):
                    continue

    def reset_values(self, new_values: list[list[Any]] | None) -> None:
        """Replace the dataset and reset virtual sorting state and row IDs."""
        self._values = [list(row) for row in new_values] if new_values is not None else []
        self._row_ids = list(range(len(self._values)))
        self._next_row_id = len(self._values)
        self._row_indexes = list(range(len(self._values)))
        self._sort_col = None
        self._sort_ascending = True

    def get_storage_index(self, display_row: int) -> int:
        """Translate a visual display row index to its storage index in memory."""
        if not (0 <= display_row < len(self._row_indexes)):
            raise IndexError(f"Display row index {display_row} out of range [0, {len(self._row_indexes)})")
        return self._row_indexes[display_row]

    def get_row_id(self, display_row: int) -> int:
        """Return the permanent row ID for a given visual display row."""
        storage_idx = self.get_storage_index(display_row)
        return self._row_ids[storage_idx]

    def get_display_row(self, row_id: int) -> int:
        """Translate a permanent row ID to its current visual display index."""
        try:
            storage_idx = self._row_ids.index(row_id)
        except ValueError as err:
            raise IndexError(f"Row ID {row_id} not found in active dataset") from err
        return self._row_indexes.index(storage_idx)

    def get_row_by_id(self, row_id: int) -> list[Any]:
        """Return a copy of the record matching the specified permanent row ID."""
        try:
            storage_idx = self._row_ids.index(row_id)
        except ValueError as err:
            raise IndexError(f"Row ID {row_id} not found in active dataset") from err
        return list(self._values[storage_idx])

    def get_row(self, display_row: int) -> list[Any]:
        """Return a copy of the record at the specified display index."""
        storage_idx = self.get_storage_index(display_row)
        return list(self._values[storage_idx])

    def get_cell(self, display_row: int, col_index: int) -> Any:
        """Return the value of the cell at display row and column."""
        row_data = self.get_row(display_row)
        if not (0 <= col_index < len(row_data)):
            raise IndexError(f"Column index {col_index} out of range [0, {len(row_data)})")
        return row_data[col_index]

    def get_all_rows(self) -> list[list[Any]]:
        """Return all rows arranged in their current visual display order."""
        return [list(self._values[storage_idx]) for storage_idx in self._row_indexes]

    def update_cell(self, display_row: int, col_index: int, value: Any) -> tuple[Any, int]:
        """Update a single cell value in storage.

        Returns:
            A tuple of (old_value, row_id).
        """
        storage_idx = self.get_storage_index(display_row)
        row_data = self._values[storage_idx]

        while len(row_data) <= col_index:
            row_data.append("")

        old_value = row_data[col_index]
        row_data[col_index] = value
        return old_value, self._row_ids[storage_idx]

    def update_row(self, display_row: int, values: list[Any], total_cols: int | None = None) -> tuple[list[Any], int]:
        """Update an entire row in storage at display_row.

        Args:
            display_row: Visual display row index.
            values: New column values for the row.
            total_cols: Optional minimum column count to pad missing columns with empty strings.

        Returns:
            A tuple of (old_row_values, row_id).
        """
        storage_idx = self.get_storage_index(display_row)
        old_values = list(self._values[storage_idx])
        new_row = list(values)
        if total_cols is not None and len(new_row) < total_cols:
            new_row.extend([""] * (total_cols - len(new_row)))
        self._values[storage_idx] = new_row
        return old_values, self._row_ids[storage_idx]

    def insert_row(
        self,
        display_index: int | None,
        row_values: list[Any] | None,
        total_cols: int,
    ) -> tuple[int, int]:
        """Insert a row at the requested display index (or append if None).

        Returns:
            A tuple of (visual_insert_index, row_id).
        """
        if display_index is not None and self._sort_col is not None:
            self.freeze_sort()

        if row_values is None:
            new_record = ["" for _ in range(total_cols)]
        else:
            new_record = list(row_values)
            if len(new_record) < total_cols:
                new_record.extend([""] * (total_cols - len(new_record)))

        storage_insert_pos = len(self._values)
        new_row_id = self._next_row_id
        self._next_row_id += 1

        self._values.append(new_record)
        self._row_ids.append(new_row_id)

        if display_index is None or display_index >= len(self._row_indexes):
            visual_insert_pos = len(self._row_indexes)
            self._row_indexes.append(storage_insert_pos)
        else:
            visual_insert_pos = max(0, display_index)
            self._row_indexes.insert(visual_insert_pos, storage_insert_pos)

        return visual_insert_pos, new_row_id

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
        kept_row_ids: list[int] = []
        old_to_new_storage_map: dict[int, int] = {}
        new_storage_idx = 0

        for old_idx, row_data in enumerate(self._values):
            if old_idx not in storage_to_delete:
                kept_values.append(row_data)
                kept_row_ids.append(self._row_ids[old_idx])
                old_to_new_storage_map[old_idx] = new_storage_idx
                new_storage_idx += 1

        self._values = kept_values
        self._row_ids = kept_row_ids

        new_row_indexes: list[int] = []
        for display_idx, old_storage in enumerate(self._row_indexes):
            if display_idx not in valid_targets:
                new_row_indexes.append(old_to_new_storage_map[old_storage])

        self._row_indexes = new_row_indexes
        return valid_targets

    def extract_sort_value(self, raw_val: Any, col: int) -> Any:
        """Convert a cell value into a normalized, comparable sort key without crashing."""
        key = self._sort_key_cols.get(col, self._sort_key_default)

        if callable(key):
            try:
                return key(raw_val)
            except Exception:
                return str(raw_val).lower()

        if key == "int":
            try:
                return int(raw_val)
            except (ValueError, TypeError):
                cleaned = "".join(ch for ch in str(raw_val) if ch.isdigit() or ch == "-")
                try:
                    return int(cleaned) if cleaned and cleaned != "-" else 0
                except ValueError:
                    return 0

        if key == "float":
            try:
                return float(raw_val)
            except (ValueError, TypeError):
                cleaned = "".join(ch for ch in str(raw_val) if ch.isdigit() or ch in ".-")
                try:
                    return float(cleaned) if cleaned and cleaned not in (".", "-", ".-") else 0.0
                except ValueError:
                    return 0.0

        if key == "date":
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

    def freeze_sort(self) -> None:
        """Lock current visual sorted order into storage and reset sort flags while preserving row IDs."""
        if self._sort_col is None:
            return
        self._values = [self._values[i] for i in self._row_indexes]
        self._row_ids = [self._row_ids[i] for i in self._row_indexes]
        self._row_indexes = list(range(len(self._values)))
        self._sort_col = None
        self._sort_ascending = True
