# CTkTable API Reference

A fast, modern data table widget for CustomTkinter with built-in sorting, selection, and in-place cell editing.

> For practical recipes and usage walkthroughs, see the [CTkTable User Guide](table_user_guide.md).

![CTkTable Preview](assets/table_preview.jpg)


---

## Table of Contents
1. [Quickstart](#1-quickstart)
2. [Arguments](#2-arguments)
   - [Widget Frame & Layout](#widget-frame--layout)
   - [Column Headers](#column-headers)
   - [Dataset, Rows & Columns](#dataset-rows--columns)
   - [Selection & Interaction](#selection--interaction)
   - [In-Place Cell Editing](#in-place-cell-editing)
3. [Methods](#3-methods)
   - [Configuration & Inspection](#configuration--inspection)
   - [Data & Row Operations](#data--row-operations)
   - [Selection Management](#selection-management)
   - [Sorting](#sorting)
   - [Viewport & Navigation](#viewport--navigation)
   - [Cell Editing Methods](#cell-editing-methods)
   - [Clipboard & Shortcuts](#clipboard--shortcuts)
   - [Event Binding](#event-binding)
4. [Read-Only Properties](#4-read-only-properties)

---

## 1. Quickstart

```python
import customtkinter as ctk

from ctkforge import CTkTable

app = ctk.CTk()

table = CTkTable(
    app,
    headers=["ID", "Name", "Role", "Salary"],
    values=[
        [1, "Ada Lovelace", "Mathematician", "£120,000"],
        [2, "Alan Turing", "Cryptanalyst", "£135,000"],
        [3, "Grace Hopper", "Computer Scientist", "£130,000"],
    ],
    selection_mode="extended",
    editable=True,
    justify={"default": "left", 0: "center", 3: "right"},
    font={1: "bold"},
    text_color={3: "#2ecc71"},
    header_alignment="center",
    header_hover_color=("#3a7ebf", "#1f538d"),
)
table.pack(fill="both", expand=True, padx=20, pady=20)

app.mainloop()
```

---

## 2. Arguments

> [!NOTE]
> All color parameters accept either a single hex/color string (used in all modes) or a `(light_mode_color, dark_mode_color)` tuple.

### Widget Frame & Layout

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `master` | `Any` | *(required)* | Parent container widget or window (e.g. `CTk`, `CTkFrame`, `CTkTabview`). |
| `width` | `int` | `600` | Preferred widget width in logical pixels. |
| `height` | `int` | `400` | Preferred widget height in logical pixels. |
| `corner_radius` | `int \| None` | `None` | Rounds the outer frame and the top corners of the header. Defaults to theme frame radius. |
| `border_width` | `int \| None` | `None` | Outer table border line thickness. Defaults to theme frame border width. |
| `border_spacing` | `int` | `5` | Inner padding between the table border and the cells. |
| `fg_color` | `str \| tuple[str, str] \| None` | `None` | Background color for the table container (single color or `(light, dark)` tuple). Defaults to theme frame color. |
| `border_color` | `str \| tuple[str, str] \| None` | `None` | Border color for the table container (single color or `(light, dark)` tuple). Defaults to theme frame border color. |

### Column Headers

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `headers` | `list[str] \| dict[int \| str, str] \| None` | `None` | Column header titles. A sequential `list[str]` is the preferred method for initialization (e.g. `["ID", "Name"]`). Also accepts a `dict` for sparse creation or partial updates (e.g. `{1: "Full Name"}`), where unmentioned columns default to `""` (or optional `"default"` key). When `None`, column count falls back to `values[0]`. |
| `show_headers` | `bool \| None` | `None` | Master visibility toggle for the pinned header bar. When `None` (default), resolves to `True` if `headers` is provided, and `False` if omitted. When set to `True` without headers, displays blank interactive headers for column sorting and resizing. |
| `header_height` | `int` | `32` | Height of the top pinned header in logical pixels (minimum 20). |
| `header_fg_color` | `str \| tuple[str, str] \| None` | `None` | Background fill color for the pinned column header bar (single color or `(light, dark)` tuple). Defaults to theme top frame color (`theme["CTkFrame"]["top_fg_color"]`). |
| `header_text_color` | `str \| tuple[str, str] \| dict \| None` | `None` | *(Scoped Attribute)* Text color for column header titles. Accepts a single color or `(light, dark)` tuple (e.g. `"#3B8ED0"` or `("#1a1a1a", "#ffffff")`) or a dict for per-header overrides by index or header title (e.g. `{"default": "#3B8ED0", 3: "#E06C75", "Salary": "#E06C75"}`). Defaults to theme label text color. |
| `header_font` | `tuple \| CTkFont \| str \| dict \| None` | `None` | *(Scoped Attribute)* Font for column headers (accepts a font tuple, `CTkFont`, or shortcuts `"bold"`, `"italic"`, `"bold italic"`). Accepts a single font (e.g. `"bold"`) or a dict for per-header overrides by index or header title (e.g. `{"default": ("Arial", 12), 0: "bold", "ID": "bold"}`). Defaults to active theme bold font (`CTkFont(weight="bold")`). |
| `header_hover_color` | `str \| tuple[str, str] \| None` | `None` | Hover tint for sortable column headers (single color or `(light, dark)` tuple). When `None` (default), hover effect is disabled. |
| `header_alignment` | `str \| dict` | `"left"` | *(Scoped Attribute)* Alignment of header titles (`"left"`, `"center"`, `"right"`). Accepts a single string (e.g. `"center"`) or a dict for per-header overrides by index or header title (e.g. `{"default": "left", 0: "center", "ID": "center"}`). Defaults to `"left"`. |
| `header_sortable` | `bool \| dict[int \| str, bool]` | `True` | *(Scoped Attribute)* Column header click sorting control. Accepts a single boolean (e.g. `False`) or a dict for per-header overrides by index or header title (e.g. `{"default": False, 2: True, "Age": True}`). Defaults to `True`. If `"default"` is omitted in reconfigures, the active baseline is preserved. |

### Dataset, Rows & Columns

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `values` | `list[list[Any]] \| None` | `None` | 2D list of row records representing the dataset. When `headers` is omitted, the length of the first row determines the column count. |
| `show_columns` | `bool \| dict[int \| str, bool]` | `True` | *(Scoped Attribute)* Column visibility toggle. Accepts a boolean (e.g. `False`) or a dict for per-column overrides by index or header title (e.g. `{"default": True, 0: False, "Salary": False}`). Hidden columns are not displayed, but their data remains in the table. Defaults to `True`. |
| `column_widths` | `int \| str \| dict \| None` | `None` | *(Scoped Attribute)* Column widths in logical pixels or `"auto"` flex space. When `None` (default) or `"auto"`, columns flex with window resizing until manually resized. Accepts an int (e.g. `120`), `"auto"`, or a dict for per-column overrides by index or header title (e.g. `{"default": "auto", 0: 90, "Age": 130}`). |
| `sort_key` | `str \| Callable \| dict \| None` | `None` | *(Scoped Attribute)* Key for column sorting (`"str"`, `"int"`, `"float"`, `"date"`, or any custom `Callable`). Accepts a single sort key (e.g. `"int"`) or a dict for per-column overrides by index or header title (e.g. `{"default": "str", 0: "int", "Age": "int"}`). Defaults to `"str"`. |
| `justify` | `str \| dict \| None` | `None` | *(Scoped Attribute)* Body cell text alignment (`"left"`, `"center"`, `"right"`). Accepts a single string (e.g. `"center"`) or a dict for per-column overrides by index or header title (e.g. `{"default": "left", 3: "right", "Salary": "right"}`). Defaults to `"left"`. |
| `text_color` | `str \| tuple[str, str] \| dict \| None` | `None` | *(Scoped Attribute)* Cell text color. Accepts a single color or `(light, dark)` tuple (e.g. `"#2ecc71"` or `("gray10", "#DCE4EE")`) or a dict for per-column overrides by index or header title (e.g. `{"default": ("gray10", "#DCE4EE"), 3: "#2ecc71", "Status": "#2ecc71"}`). Defaults to theme label text color. |
| `font` | `tuple \| CTkFont \| str \| dict \| None` | `None` | *(Scoped Attribute)* Font for table body cells (accepts a font tuple, `CTkFont`, or shortcuts `"bold"`, `"italic"`, `"bold italic"`). Accepts a single font (e.g. `"italic"`) or a dict for per-column overrides by index or header title (e.g. `{"default": ("Arial", 12), 1: "bold", "Name": "bold"}`). Defaults to active theme font (`CTkFont()`). |
| `row_height` | `int` | `28` | Height of each body row in logical pixels (minimum 16). |
| `row_color` | `str \| tuple[str, str] \| None` | `None` | Base row background color (single color or `(light, dark)` tuple). Defaults to container `fg_color` (uniform flat look). |
| `alternate_row_color` | `str \| tuple[str, str] \| None` | `None` | Odd row background color for opt-in zebra striping (single color or `(light, dark)` tuple). Defaults to `None` (matches `row_color`, no striping). |

### Selection & Interaction

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `selection_target` | `str` | `"row"` | What gets highlighted on click: `"row"` (entire line) or `"cell"` (individual box). |
| `selection_mode` | `str` | `"single"` | Selection behavior: `"single"` (one item), `"extended"` (Shift/Ctrl range & multi-select), or `"none"` (disabled). |
| `selected_color` | `str \| tuple[str, str] \| None` | `None` | Highlight fill color for selected items (single color or `(light, dark)` tuple). Defaults to active theme button color. |
| `selected_text_color` | `str \| tuple[str, str] \| None` | `None` | Text color for selected items (single color or `(light, dark)` tuple). Defaults to active theme button text color. |
| `command` | `Callable \| None` | `None` | Callback fired whenever selection changes: `def on_select(items): ...` |
| `copyable` | `bool` | `False` | Master toggle for interactive `Ctrl+C` clipboard copying. Disabled by default. |

### In-Place Cell Editing

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `editable` | `bool \| dict[int \| str, bool]` | `False` | *(Scoped Attribute)* In-place cell editing control. Accepts a single boolean (e.g. `True`) or a dict for per-column overrides by index or header title (e.g. `{"default": True, 0: False, "ID": False}`). Defaults to `False`. If `"default"` is omitted in reconfigures, the active baseline is preserved. |
| `on_cell_edit` | `Callable \| None` | `None` | Callback fired on edit commit: `def on_edit(actual_row, col, old_val, new_val): ...` |


---

## 3. Methods

All options can be updated dynamically via `.configure()` and queried via `.cget()`.

### Configuration & Inspection

#### `.configure(**kwargs) -> None`
Configures widget options dynamically and refreshes the canvas in a single batched pass.
```python
# Update dataset, layout, and styling at runtime:
table.configure(
    values=[["Alice", 28], ["Bob", 34]],
    row_height=32,
    row_color=("#f9f9f9", "#1f1f1f"),
    alternate_row_color=("#f0f0f0", "#262626"),
    selection_mode="single",
)
```

#### `.cget(attribute_name: str) -> Any`
Reads the current value of any widget configuration option.
```python
current_height = table.cget("row_height")
current_values = table.cget("values")
row_bg = table.cget("row_color")
```

---

### Data & Row Operations

#### `.get(row: int | None = None, column: int | None = None) -> Any`
Returns table data in the current visual display order (respecting active sorting):
- If `row=None` and `column=None`: returns the complete 2D list of all rows in current visual order (ideal for exports).
- If `row` is specified and `column=None`: returns that single row (equivalent to `.get_row(row)`).
- If `row` and `column` are both specified: returns that single cell value (equivalent to `.get_cell(row, col)`).
- If `row=None` and `column` is specified: returns a list of all values in that column.
```python
# Export the entire dataset in current visual sorted order:
visible_data = table.get()

# Get specific visual row or cell:
top_row = table.get(row=0)
first_name = table.get(0, 1)
```

#### `.insert_row(index: int | None = None, values: list[Any] | None = None) -> int`
Inserts a new record into the dataset.
- If `index=None`: appends the row to the dataset (respecting any active column sort).
- If `index` is specified: automatically freezes any active sort into static manual order (`freeze_sort()`) and inserts the record directly at that visual row position so it stays in place.
- Returns the new display index.
```python
# Append to end (or sorted slot if sorted):
new_idx = table.insert_row(values=[4, "John von Neumann", "Polymath", "$150,000"])

# Insert at specific visual position (freezes sort):
top_idx = table.insert_row(index=0, values=[5, "Grace Hopper", "Scientist", "$160,000"])
```

#### `.delete_rows(row_indexes: list[int] | set[int] | int) -> None`
Deletes one or multiple rows in a single batch. Updates internal sort maps, clamps scroll positions, and cleans up selection sets.
```python
table.delete_rows(2)  # Delete single row
table.delete_rows([0, 1, 3])  # Delete multiple rows in one operation
```

#### `.update_cell(row_index: int, col_index: int, value: Any, notify: bool = True) -> None`
Updates a cell value in-place. If the table is actively sorted by `col_index`, the sort order is refreshed automatically.
```python
table.update_cell(0, 3, "$140,000")
```

#### `.update_row(display_row: int, values: list[Any], notify: bool = True) -> None`
Atomically updates an entire row record in-place. If the table is actively sorted by one of the modified columns, the sort order refreshes automatically.
```python
table.update_row(0, [1, "Ada Lovelace", "Mathematician", "£150,000"])
```

#### `.get_header(col_index: int) -> str`
Returns the title text for the specified column header.
```python
title = table.get_header(1)  # e.g. "Name"
```

#### `.set_header(col_index: int, title: str) -> None`
Updates the title for a specific column header without re-supplying the entire list.
```python
table.set_header(1, "Full Name")
```

#### `.get_row_id(display_row: int | Sequence[int]) -> int | list[int]`
Translates one or multiple visual display row indexes to their permanent, immutable row IDs (assigned at load/insert time).
```python
# Pass a single visual row index:
row_id = table.get_row_id(disp_row_index)  # e.g. disp_row_index = 0 --> row_id = 42

# Or pass a list of visual row indexes (e.g. from selection):
selected_rows = table.get_selected_rows()  # e.g. [0, 1]
row_ids = table.get_row_id(selected_rows)  # e.g. [42, 105]
```

#### `.get_display_row(row_id: int | Sequence[int]) -> int | list[int]`
Translates one or multiple permanent row IDs to their current visual display row indexes on screen.
```python
# Pass a single row ID to locate where it sits right now:
disp_row_index = table.get_display_row(42)
table.select_row(disp_row_index)
table.scroll_to(row=disp_row_index)

# Or translate multiple row IDs at once:
disp_row_indexes = table.get_display_row([42, 105])  # e.g. [0, 2]
```

#### `.get_row_by_id(row_id: int) -> list[Any]`
Returns a copy of the record values matching a specific permanent row ID, regardless of current visual sort or scroll position.
```python
record = table.get_row_by_id(42)  # Returns data for record 42 directly
```

#### `.get_row(row_index: int) -> list[Any]`
Returns a copy of the row record at the specified visual display index.
```python
record = table.get_row(0)  # e.g. [1, "Ada Lovelace", "Mathematician", "$120,000"]
```

#### `.get_cell(row_index: int, col_index: int) -> Any`
Returns the single cell value at display position `(row_index, col_index)`.
```python
name = table.get_cell(0, 1)  # "Ada Lovelace"
```

---

### Selection Management

#### `.get_selected_rows() -> list[int]`
Returns a sorted list of selected display row indexes.
- In row selection mode: returns all selected rows.
- In cell selection mode: returns the deduplicated rows containing any selected cells.
```python
selected_rows = table.get_selected_rows()  # e.g. [0, 2]
```

#### `.get_selected_cells() -> list[tuple[int, int]]`
Returns a sorted list of selected `(row, col)` cell coordinates.
- In cell selection mode: returns all explicitly selected cells.
- In row selection mode: returns all cell coordinates across the selected rows.
```python
selected_cells = table.get_selected_cells()  # e.g. [(0, 1), (0, 2)]
```

#### `.select_row(row_index: int, notify: bool = True) -> None`
Selects a specific row by its display index.
```python
table.select_row(0)
```

#### `.deselect_row(row_index: int, notify: bool = True) -> None`
Removes a specific row from the selection set.
```python
table.deselect_row(0)
```

#### `.select_cell(row_index: int, col_index: int, notify: bool = True) -> None`
Selects an individual cell at `(row_index, col_index)`.
```python
table.select_cell(2, 3)
```

#### `.select_all(notify: bool = True) -> None`
Selects all rows (or all cells) across the entire table.
```python
table.select_all()
```

#### `.clear_selection(notify: bool = True) -> None`
Deselects all rows and cells.
```python
table.clear_selection()
```

---

### Sorting

#### `.sort_by(column_index: int, ascending: bool = True) -> None`
Sorts the table by the specified column using zero-reshuffle index mapping. Raw data is never moved.
```python
table.sort_by(0, ascending=True)  # Sort column 0 ascending (A-Z)
table.sort_by(2, ascending=False)  # Sort column 2 descending (Z-A)
```

#### `.clear_sort() -> None`
Resets the table back to its baseline insertion order (as long as a sort was not frozen with `.freeze_sort()`).
```python
table.clear_sort()
```

#### `.freeze_sort() -> None`
Freezes the current visual sorted order into the baseline dataset and resets the active sort state without altering any permanent `row_id` identities. Header sort arrows (▲ / ▼) are cleared, and inserting or editing cells will no longer trigger automatic re-sorting.
```python
table.sort_by(1, ascending=True)  # Sort by column 1
table.freeze_sort()  # Freeze this visual layout as manual baseline
print(table.cget("values"))  # Baseline data matches frozen visual order
```

#### `.get_sort_state() -> tuple[int | None, bool]`
Returns the currently sorted column index and direction: `(col_index, is_ascending)`.
```python
col, is_asc = table.get_sort_state()
print(f"Sorted on col {col}, Ascending: {is_asc}")
```

---

### Viewport & Navigation

#### `.scroll_to(row: int | None = None, col: int | str | None = None) -> None`
Scrolls the table viewport to bring the specified display row or column (by index or header title) into view.
```python
table.scroll_to(row=1500)  # Scroll vertically to row 1500
table.scroll_to(row=0, col=5)  # Jump to top row, column 5
table.scroll_to(col="Status")  # Jump to "Status" column
```

#### `.auto_fit_column(col_index: int | str) -> None`
Measures the text of all rows and the header title for the given column (by index or header title) using font metrics, and adjusts the column width to fit content with padding.
```python
table.auto_fit_column(1)  # Fit column 1 to longest text
table.auto_fit_column("Department")  # Fit by header title
```

#### `.auto_fit_columns(columns: list[int | str] | None = None) -> None`
Measures and fits column widths for all columns (or a specified list of column indexes or header titles) in a single batched pass with one redraw cycle.
```python
table.auto_fit_columns()  # Fit all columns to content on load
table.auto_fit_columns([0, 1, "Salary"])  # Fit specific subset of columns
```

---

### Cell Editing Methods

#### `.start_editing(row: int, col: int) -> None`
Programmatically mounts the floating `CTkEntry` editor over the target cell.
```python
table.start_editing(0, 1)  # Open editor on row 0, col 1
```

#### `.edit_focused_cell() -> None`
Opens the editor on the cell that currently has keyboard focus.
```python
table.edit_focused_cell()
```

---

### Clipboard & Shortcuts

#### `.copy_selection() -> str`
Copies currently highlighted rows or cells to the system clipboard as Tab-Separated Values (TSV) with newlines and returns the string. Pastes directly into Excel or text editors.
- In row selection mode (`selection_target="row"`): exports the entire underlying row record from memory (including trailing hidden fields if surplus, or only existing items if short).
- In cell selection mode (`selection_target="cell"`): exports only highlighted visible cells (missing items in short rows export as empty strings).
```python
tsv_text = table.copy_selection()
```

---

### Event Binding

#### `.bind(sequence: str | None = None, command: Callable | None = None, add: bool = True) -> None`
Registers a keyboard or mouse shortcut. Events are automatically forwarded to the internal canvas so hotkeys work when the table has keyboard focus.
```python
# Bind custom shortcut to table:
table.bind("<F2>", lambda _e: table.edit_focused_cell())
```

---

## 4. Read-Only Properties

```python
is_editing = table.is_editing
```
