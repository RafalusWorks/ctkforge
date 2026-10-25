# CTkTable User Guide

Comprehensive implementation guide for structuring, styling, configuring, and manipulating tabular data in `CTkTable`.

> For technical signatures, default values, and parameter types, see the [CTkTable API Reference](table.md).

---

## Table of Contents
1. [Setup & Geometry](#1-setup--geometry)
   - [Determining Columns & Headers](#determining-columns--headers)
   - [Column Widths & Auto-Fitting](#column-widths--auto-fitting)
2. [Visual Styling & Typography](#2-visual-styling--typography)
   - [Row Theming & Zebra Striping](#row-theming--zebra-striping)
   - [Per-Column & Header Alignment](#per-column--header-alignment)
   - [Text Colors & Theme Tuples](#text-colors--theme-tuples)
   - [Fonts & Typography Shortcuts](#fonts--typography-shortcuts)
   - [Header Hover Highlights](#header-hover-highlights)
3. [Selection & Clipboard](#3-selection--clipboard)
   - [Selection Target & Modes](#selection-target--modes)
   - [Reading & Modifying Selection State](#reading--modifying-selection-state)
   - [Clipboard Integration](#clipboard-integration)
4. [Sorting & In-Place Editing](#4-sorting--in-place-editing)
   - [Interactive & Programmatic Sorting](#interactive--programmatic-sorting)
   - [Column Sort Keys](#column-sort-keys)
   - [In-Place Cell Editing](#in-place-cell-editing)
5. [Runtime Data Operations](#5-runtime-data-operations)
   - [Inserting, Updating & Deleting Records](#inserting-updating--deleting-records)
   - [Managing Column Headers](#managing-column-headers)
   - [Display Indexes vs. Raw Storage Indexes](#display-indexes-vs-raw-storage-indexes)
   - [Reading & Exporting Data](#reading--exporting-data)
6. [User Interaction Reference & Complete Recipe](#6-user-interaction-reference--complete-recipe)
   - [Keyboard & Mouse Controls Reference](#keyboard--mouse-controls-reference)
   - [Complete Working Recipe](#complete-working-recipe)

---

## 1. Setup & Geometry

### Determining Columns & Headers

`CTkTable` determines its active column count dynamically without requiring a separate column count parameter:

* **From `headers` (Primary)**: The number of items in `headers` sets the column count. Accepts a sequential list (`["ID", "Name", "Role"]`) or a dictionary for sparse definitions (`{0: "ID", 2: "Role"}`). Unmentioned columns default to `""` (or the optional `"default"` key). Trailing values exceeding the column count remain in the dataset but are hidden from display.
* **From `values` (Fallback)**: When `headers` is omitted or `None`, the length of the first data row (`values[0]`) sets the column count.
* **Empty Table**: If neither `headers` nor `values` is supplied, the table initializes with `0` columns.
* **Column Visibility (`show_columns`)**: Control whether all columns or specific columns are displayed. Accepts a boolean (`show_columns=True` or `False`) or a scoped dictionary with header titles or column indexes (`show_columns={"default": True, "Salary": False, 0: False}`). Hidden columns are not displayed, but their data remains in the table.

```python
import customtkinter as ctk
from ctkforge import CTkTable

app = ctk.CTk()

# 1. Standard list initialization (preferred method):
table1 = CTkTable(app, headers=["ID", "Name", "Role"])

# 2. Sparse dictionary initialization:
table2 = CTkTable(app, headers={"default": "N/A", 0: "ID", 1: "User"})

# 3. Headerless table with visible interactive header cells:
table3 = CTkTable(app, values=[[1, "Alice"], [2, "Bob"]], show_headers=True)

# 4. Column visibility overrides (hide specific columns by title or index):
table4 = CTkTable(
    app,
    headers=["ID", "Name", "Department", "Salary"],
    values=[[101, "Alice", "Engineering", 120000]],
    show_columns={"Salary": False},
)

# Dynamically toggle column visibility in code:
table4.configure(show_columns={"Salary": True, "Department": False})
```

### Column Widths & Auto-Fitting

Column sizing is controlled via the scoped attribute `column_widths`:
* **`"auto"` (Default)**: Evenly distributes available table width across columns and flexes with window resizing. The moment any column is manually dragged or auto-fitted, all columns freeze at their current rendered pixel widths—expanding a column pushes trailing columns to the right into the horizontal scroll area rather than squishing neighboring columns.
* **Integer Pixel Width**: Assigns a fixed pixel width across all columns (e.g. `column_widths=120`).
* **Dictionary Override**: Configures specific column widths by header title, column index, or both, with an optional `"default"` fallback:
  ```python
  # Configure by header title, column index, or both:
  table = CTkTable(
      app,
      headers=["ID", "Description", "Price"],
      column_widths={"default": "auto", "ID": 80, 2: 110},
  )
  ```

> [!TIP]
> To unfreeze columns and restore dynamic window flexing after manual resizing, reconfigure the table:
> ```python
> table.configure(column_widths="auto")
> ```

#### Auto-Fitting Columns in Code
To measure cell content and snap columns to fit text without manual pixel calculations, call auto-fit methods:
```python
# Auto-fit all visible columns in a single pass:
table.auto_fit_columns()

# Or auto-fit specific columns by header title or index:
table.auto_fit_column("Description")
table.auto_fit_columns(["ID", 2])
```

Users can also manually resize columns by dragging header divider lines or double-clicking any divider to auto-fit that column to content.

---

## 2. Visual Styling & Typography

All color parameters accept either a single hex string (e.g. `"#3B8ED0"`) or a `(light_mode, dark_mode)` tuple (e.g. `("gray10", "#DCE4EE")`).

### Row Theming & Zebra Striping

By default, body rows use the table's `fg_color`. You can assign a custom row background color or opt into alternating zebra striping:

```python
table = CTkTable(
    app,
    ...,
    row_color=("#ffffff", "#1e1e1e"),  # Base row background
    alternate_row_color=("#f9f9f9", "#262626"),  # Odd row background (zebra striping)
)
```

### Per-Column & Header Alignment

Configure text alignment using `"left"`, `"center"`, or `"right"` via the scoped attributes `justify` (body cells) and `header_alignment` (headers):

```python
table = CTkTable(
    app,
    headers=["ID", "Item", "Quantity", "Price", "Status"],
    values=data,
    # Body cell alignment:
    justify={
        "default": "left",
        0: "center",
        2: "center",
        3: "right",
        4: "center",
    },
    # Center all column headers:
    header_alignment="center",
)
```

### Text Colors & Theme Tuples

Set text colors globally or per column using the scoped attributes `text_color` and `header_text_color`:

```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    # Body text color: override price column with green, status with amber:
    text_color={
        3: ("#1b7a37", "#2ecc71"),  # Emerald highlight for Price
        4: ("#8a6d00", "#f1c40f"),  # Amber highlight for Status
    },
    # Header text color: set fallback and override column 0:
    header_text_color={
        "default": "#3B8ED0",
        0: "#E06C75",
    },
)
```

### Fonts & Typography Shortcuts

The scoped attributes `font` and `header_font` accept font tuples `("Family", size, "weight")`, `CTkFont` instances, or convenient string shortcuts (`"bold"`, `"italic"`, `"bold italic"`):

```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    # Make Price column bold using shortcut string:
    font={3: "bold"},
    # Custom font on header column 0:
    header_font={0: ("Segoe UI", 13, "bold")},
)
```

### Header Hover Highlights

Highlight sortable column headers on hover by setting `header_hover_color`:

```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    header_hover_color=("#3a7ebf", "#1f538d"),
)
```

---

## 3. Selection & Clipboard

### Selection Target & Modes

Selection behavior is controlled by two parameters:

```python
table = CTkTable(
    app,
    selection_target="row",  # "row" (entire line) or "cell" (individual box)
    selection_mode="extended",  # "extended", "single", or "none"
)
```

* **`selection_target`**:
  * `"row"` *(default)*: Clicks highlight the entire horizontal row across all columns. Recommended for record lists and administrative panels.
  * `"cell"`: Clicks highlight only the targeted individual cell. Recommended for spreadsheets and numeric entry.

* **`selection_mode`**:
  * `"extended"` *(default)*: Full multi-selection support with `Ctrl+Click` (cherry-pick), `Shift+Click` (continuous range), `Ctrl+A` (select all), and `Shift+Up/Down` (extend selection).
  * `"single"`: Restricts selection to exactly one item at any time.
  * `"none"`: Disables interactive and visual selection completely (suitable for read-only status monitors and logs).

### Reading & Modifying Selection State

Query or update selection programmatically:

```python
# Returns sorted list of selected display row indexes, e.g. [0, 2, 5]:
selected_rows = table.get_selected_rows()

# Returns sorted list of selected (row, column) coordinates, e.g. [(0, 1), (2, 3)]:
selected_cells = table.get_selected_cells()

# Select or deselect a specific row:
table.select_row(0)
table.deselect_row(0)

# Clear all active selections:
table.clear_selection()
```

#### Selection Event Callback
Listen for selection changes using the `command` parameter:

```python
def on_selection(items):
    print("Active selection:", items)


table = CTkTable(app, command=on_selection)
```

### Clipboard Integration

Set `copyable=True` to enable clipboard export:

```python
table = CTkTable(app, copyable=True)
```

* **Keyboard Shortcut**: Press **`Ctrl + C`** while focused on the table to copy selected items to the clipboard.
* **Format**: Data is formatted as standard Tab-Separated Values (TSV) with newlines, enabling clean pastes directly into Microsoft Excel, Google Sheets, or text editors.
* **Row vs. Cell Copy Scope**:
  * In **row mode** (`selection_target="row"`): copies the entire underlying row record from memory. If a row contains extra hidden fields beyond the visible column count, those trailing values are included. If a row contains fewer values than the column count, only the existing items are copied.
  * In **cell mode** (`selection_target="cell"`): copies only the explicitly selected visible cells (missing items in short rows are exported as empty strings).
* **Programmatic Copy**: Call `table.copy_selection()` to export the TSV string in code:
  ```python
  tsv_output = table.copy_selection()
  ```

---

## 4. Sorting & In-Place Editing

### Interactive & Programmatic Sorting

Clicking a column header cycles through 3 sorting states:
1. **1st Click**: Sorts **Ascending** (`▲`).
2. **2nd Click**: Sorts **Descending** (`▼`).
3. **3rd Click**: **Clears Sort** (restores original baseline dataset order).

#### Enabling & Restricting Header Sorting (`header_sortable`)
Control click sorting globally or per column via the scoped attribute `header_sortable`:
* `header_sortable=True`: All column headers are sortable (default).
* `header_sortable={0: False}`: All columns sortable except column 0.
* `header_sortable={"default": False, 2: True}`: All columns locked except column 2.

> When reconfiguring with a dictionary, omitting `"default"` preserves the active baseline.

#### Programmatic Sorting API
Disabling header clicks only restricts user mouse interactions. You can sort any column programmatically:

```python
# Sort column 2 descending:
table.sort_by(2, ascending=False)

# Restore original baseline order:
table.clear_sort()

# Freeze current sorted visual layout as static manual order:
table.freeze_sort()

# Inspect current sort column and direction:
sort_col, is_ascending = table.get_sort_state()  # e.g. (2, False)
```

### Column Sort Keys

Declare explicit comparison types per column using the scoped attribute `sort_key`:

```python
table = CTkTable(
    app,
    headers=["ID", "Name", "Salary", "Joined"],
    sort_key={
        "default": "str",  # Case-insensitive alphabetical
        0: "int",  # Integer comparison (10 sorts after 2)
        2: "float",  # Strips currency symbols and compares decimals
        3: "date",  # Chronological order for ISO format (YYYY-MM-DD)
    },
)
```

| Key | Comparison Mode | Example Transformation | Fallback |
| :--- | :--- | :--- | :--- |
| `"str"` *(default)* | Case-insensitive alphabetical | `"Alice"`, `"bob"` → `"alice"`, `"bob"` | `""` |
| `"int"` | Strips formatting, compares integers | `"$1,420"`, `"-50kg"` → `1420`, `-50` | `0` |
| `"float"` | Strips currency/percent, compares floats | `"£1,420.50"`, `"99.9%"` → `1420.50`, `99.9` | `0.0` |
| `"date"` | Chronological ISO date comparison | `"2026-03-15"` < `"2026-10-23"` | `""` |

#### Custom Sort Functions
Pass any `Callable[[Any], Any]` to define custom sorting logic:

```python
PRIORITY_ORDER = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}


def priority_key(val: str) -> int:
    return PRIORITY_ORDER.get(val, -1)


table = CTkTable(app, headers=["Task", "Priority"], sort_key={1: priority_key})
```

### In-Place Cell Editing

Enable interactive text editing across the table or on specific columns using the scoped attribute `editable`:

* `editable=False`: Table is read-only (default).
* `editable=True`: All cells are editable.
* `editable={"default": True, 0: False}`: All columns editable except locked primary key column 0.
* `editable={1: True, 2: True}`: Only columns 1 and 2 are editable.

```python
table = CTkTable(
    app,
    headers=["ID", "Name", "Role"],
    editable={"default": True, 0: False},
)
```

#### How Editing Works
* **Trigger**: Double-click any cell or press **`Enter`** on a focused cell.
* **Commit**: Press **`Enter`** or click outside the cell (`FocusOut`).
* **Cancel**: Press **`Escape`** to discard changes.

#### Commit Callback (`on_cell_edit`)
Hook into edit commits to trigger database syncs or validations:

```python
def handle_cell_edit(storage_row: int, col: int, old_val: str, new_val: str) -> None:
    print(f"Row {storage_row}, Col {col} changed from '{old_val}' to '{new_val}'")


table = CTkTable(app, on_cell_edit=handle_cell_edit)
```

#### Binding Custom Edit Keys (e.g. `F2`)
By default, function keys (`F1`–`F12`) are left free for application-wide shortcuts. To enable `F2` for in-place editing:

```python
table.bind("<F2>", lambda _event: table.edit_focused_cell())
```

---

## 5. Runtime Data Operations

### Inserting, Updating & Deleting Records

Modify table records directly on live datasets:

```python
# 1. Insert a new record:
# Appends to the end of dataset (respecting any active sort):
new_idx = table.insert_row(values=[105, "Grace Hopper", "Completed"])

# Or insert at a specific visual row index:
table.insert_row(index=0, values=[100, "Ada Lovelace", "Verified"])

# 2. Update an existing cell or row:
table.update_cell(row_index=0, col_index=1, value="Ada King")
table.update_row(display_row=0, values=[100, "Ada King", "Verified"])

# 3. Delete records:
# Delete a single row by index:
table.delete_rows(2)

# Or delete multiple rows in a batch (e.g. active user selection):
table.delete_rows(table.get_selected_rows())

# Bind the Delete key to remove highlighted records:
table.bind("<Delete>", lambda _e: table.delete_rows(table.get_selected_rows()))
```

### Managing Column Headers

Read or update individual header titles dynamically:

```python
# Read a header title by column index:
current_title = table.get_header(1)  # e.g. "Name"

# Update a single header title without re-supplying the entire list:
table.set_header(1, "Full Name")
```

### Display Rows vs. Permanent Row IDs (`row_id`)

`CTkTable` cleanly separates the visual screen position from the persistent identity of each record:

* **`display_row` (Visual Screen Position)**: Where the row is currently rendered on screen (`0` is the top visible row). Changes whenever the user sorts, filters, or scrolls.
* **`row_id` (Permanent Origin Identity)**: The immutable birth certificate ID assigned when the record is loaded or inserted (`0, 1, 2, ...`). It **never changes**, surviving sorting, filtering, editing, and `freeze_sort()`. This guarantees your records always remain tied to external source files or database primary keys.

```python
# 1. Translate a visual display row to its permanent row ID:
row_id = table.get_row_id(visual_row)  # e.g. visual_row 0 --> row_id 42

# 2. Translate multiple selected rows at once:
selected_ids = table.get_row_id(table.get_selected_rows())

# 3. Translate in reverse: find where record with row_id=42 is currently displayed:
disp_row = table.get_display_row(42)
table.select_row(disp_row)
table.scroll_to(row=disp_row)

# 4. Fetch the record values directly by row_id:
record = table.get_row_by_id(42)
```

### Reading & Exporting Data

Retrieve tabular data in visual sorted order or inspect raw values:

```python
# Export the full dataset in current visual sorted order (ideal for CSV export):
visible_records = table.get()

# Get all values for a single visual row:
row_record = table.get_row(0)  # or table.get(row=0)

# Get a single visual cell value:
cell_value = table.get_cell(row_index=0, col_index=1)  # or table.get(0, 1)

# Inspect original unsorted baseline dataset:
raw_dataset = table.cget("values")
```

---

## 6. User Interaction Reference & Complete Recipe

### Keyboard & Mouse Controls Reference

The following table summarizes all built-in mouse and keyboard interactions:

| Control | Event | Action |
| :--- | :--- | :--- |
| **`Up` / `Down`** | `<Up>`, `<Down>` | Move active focus up or down by 1 row. |
| **`Left` / `Right`** | `<Left>`, `<Right>` | Move active focus across columns (in Cell mode). |
| **`PageUp` / `PageDown`** | `<Prior>`, `<Next>` | Jump up or down by one visible page of rows. |
| **`Home` / `End`** | `<Home>`, `<End>` | Jump directly to the first or last row. |
| **`Space`** | `<space>` | Toggle selection on the highlighted item. |
| **`Enter`** | `<Return>` | Open in-place cell editor (or commit active edit). |
| **`Escape`** | `<Escape>` | Deselect all highlighted items (or cancel active edit). |
| **`Ctrl + C`** | `<Control-c>` | Copy selected rows or cells to system clipboard as TSV. |
| **`Ctrl + A`** | `<Control-a>` | Select all rows or cells in the table. |
| **`Mouse Wheel`** | `<MouseWheel>` | Scroll viewport vertically. |
| **`Shift + Mouse Wheel`** | `<Shift-MouseWheel>` | Scroll viewport horizontally. |
| **`Header Click`** | `<Button-1>` | Cycle column sort: Ascending (▲), Descending (▼), Clear. |
| **`Header Divider Drag`** | `<B1-Motion>` | Interactively resize column width. |
| **`Header Divider Double-Click`** | `<Double-Button-1>` | Auto-fit column width to content. |

### Complete Working Recipe

```python
import customtkinter as ctk
from ctkforge import CTkTable

app = ctk.CTk()
app.geometry("960x540")
app.title("CTkTable Demo")

headers = ["ID", "Customer Name", "Quantity", "Price", "Status"]
data = [
    [101, "Emma Watson", 4, "$120.00", "Shipped"],
    [102, "Liam Neeson", 1, "$450.00", "Pending"],
    [103, "Olivia Colman", 12, "$85.50", "Completed"],
    [104, "James Bond", 2, "$950.00", "Shipped"],
    [105, "Helen Mirren", 6, "$310.00", "Completed"],
]


def on_cell_edit(storage_row: int, col: int, old_val: str, new_val: str) -> None:
    print(f"Row {storage_row}, Col {col} changed: '{old_val}' -> '{new_val}'")


def on_selection(items) -> None:
    print("Selection changed:", items)


table = CTkTable(
    app,
    headers=headers,
    values=data,
    # Layout and sizing:
    column_widths={"default": "auto", 0: 80, 2: 90, 3: 110, 4: 120},
    row_height=30,
    header_height=34,
    # Sorting:
    header_sortable={0: False},  # Lock ID column from sorting
    sort_key={"default": "str", 0: "int", 2: "int", 3: "float"},
    # Alignment & Typography:
    justify={"default": "left", 0: "center", 2: "center", 3: "right", 4: "center"},
    font={3: "bold"},
    text_color={3: ("#1b7a37", "#2ecc71")},
    header_alignment="center",
    header_hover_color=("#3a7ebf", "#1f538d"),
    # Theming:
    alternate_row_color=("#f9f9f9", "#242424"),
    # Selection & Interaction:
    selection_target="row",
    selection_mode="extended",
    copyable=True,
    command=on_selection,
    # Editing:
    editable={1: True, 2: True, 3: True},  # Edit Name, Quantity, and Price only
    on_cell_edit=on_cell_edit,
)
table.pack(fill="both", expand=True, padx=20, pady=20)

# Optional custom keybindings:
table.bind("<F2>", lambda _e: table.edit_focused_cell())
table.bind("<Delete>", lambda _e: table.delete_rows(table.get_selected_rows()))

app.mainloop()
```
