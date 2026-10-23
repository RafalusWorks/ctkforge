# CTkTable User Guide

This guide explains how to navigate, select rows and cells, resize columns, sort data, and edit cells in the `CTkTable` widget.

---

## 1. Moving Around (Navigation)

### Using the Mouse
* **Vertical Scroll**: Spin the mouse wheel up or down. You can also drag the vertical scrollbar thumb on the right.
* **Horizontal Scroll**: Hold **`Shift`** while spinning the mouse wheel to scroll left or right. You can also drag the horizontal scrollbar at the bottom.

### Using the Keyboard
Click anywhere inside the table to focus it, then use these keys:

| Key | What it does |
| :--- | :--- |
| **`Up` / `Down`** | Move up or down by one row. |
| **`Left` / `Right`** | Move left or right across columns (when in Cell mode). |
| **`PageUp` / `PageDown`** | Jump up or down by one full visible page. |
| **`Home` / `End`** | Jump straight to the very first row or the very last row. |
| **`Space`** | Toggle selection on the currently highlighted item. |
| **`Escape`** | Deselect all highlighted items (or cancel in-place editing). |

> **Auto-Scroll:** When you navigate with the keyboard, the table automatically slides the active row or column into view. You never have to manually scroll to find your cursor.

---

## 2. Choosing What to Select (`selection_target`)

You can control whether clicks highlight entire rows or individual cells:

```python
table = CTkTable(
    ...,
    selection_target="row",  # "row" (default) or "cell"
)
```

* **`"row"` (Default)**: Clicking anywhere on a row highlights the entire horizontal stripe across all columns. Best for databases, admin dashboards, and record lists.
* **`"cell"`**: Clicking lights up only that one specific box. Best for spreadsheets, single-value copies, and in-place editing.

You can also change this at any time in code:
```python
table.configure(selection_target="cell")
```

---

## 3. How Multi-Selection Works (`selection_mode`)

You can control how many items can be selected at once:

```python
table = CTkTable(
    ...,
    selection_mode="extended",  # "extended" (default), "single", or "none"
)
```

### The Three Modes:

1. **`"extended"` (Default - Multi-Select)**:
   * **Plain Click**: Picks that row/cell and deselects any others.
   * **`Ctrl + Click`**: Cherry-picks individual items one by one without losing the ones you already selected.
   * **`Shift + Click`**: Selects a continuous block between your first pick and your second pick.
   * **`Ctrl + A`**: Selects all records or cells at once.
   * **`Shift + Up / Down`**: Extends your selection block row by row using the arrow keys.

2. **`"single"` (Single Item Only)**:
   * Only one item can ever be selected at a time.
   * `Ctrl` and `Shift` are ignored.
   * Moving with arrow keys moves the single selection directly.

3. **`"none"` (Read-Only)**:
   * Selection is turned off completely.
   * Clicks do not highlight rows or change colors. Ideal for live logs and status monitors.

---

## 4. Reading Selected Items in Code

You can read selected rows or cells at any time using dedicated methods:

```python
# Returns a list of selected row numbers, e.g. [2, 5, 6]
# (In cell mode, returns the unique rows containing selected cells):
selected_rows = table.get_selected_rows()

# Returns a list of (row, column) pairs, e.g. [(2, 0), (2, 1), (5, 3)]:
selected_cells = table.get_selected_cells()
```

You can also listen for live selection changes using the `command` callback:

```python
def on_selection_change(selected_items):
    print("User selected:", selected_items)


table = CTkTable(..., command=on_selection_change)
```

---

## 5. Resizing Column Widths

* **Manual Dragging**: Hover your mouse over the vertical divider line between any two column headers. The cursor will change to a double-headed arrow (`<->`). Click and drag left or right to make the column wider or narrower.
* **Double-Click to Auto-Fit**: Double-click any header divider line. The table will automatically measure the header text and the data in that column, snapping the width to fit the content cleanly.
* **Programmatic Auto-Fit in Code**: Call `table.auto_fit_columns()` on startup or after loading data to measure and snap all columns in a single pass without manual pixel guesses:
  ```python
  table.auto_fit_columns()  # Auto-fit all columns
  table.auto_fit_column(0)  # Or auto-fit a single specific column
  ```

---

## 6. Header Column Sorting

### How to Sort
Click any column header to cycle through three states:
1. **1st Click**: Sorts **Ascending** (indicated by `▲`).
2. **2nd Click**: Sorts **Descending** (indicated by `▼`).
3. **3rd Click**: **Clears Sort** (instantly restores original database order).

### Enabling & Restricting Header Sorting (`header_sortable`)

By default, users can click any column header to sort (`header_sortable=True`). You can control interactive sorting globally or per-column using a single argument:

* **`header_sortable=True`**: All column headers are sortable (default).
* **`header_sortable={0: False}`**: All columns sortable, **except** column 0.
* **`header_sortable={"default": False, 2: True}`**: All columns locked, **except** column 2 (only it can be sorted).

```python
table = CTkTable(
    ...,
    header_sortable={0: False},  # Sort all columns except ID
)
```

> **Baseline Preservation:** When reconfiguring with a dictionary (e.g. `table.configure(header_sortable={3: False})`), omitting `"default"` preserves whatever baseline was already active.
>
> **Programmatic Sorting Always Allowed:** Disabling header clicks only blocks interactive mouse clicks. You can still sort any column programmatically from Python code via `table.sort_by(...)` at any time.

### Column Sort Keys (`sort_key`)
Header clicks cycle through 3 states: **Ascending (▲)** → **Descending (▼)** → **Clear Sort** (restores insertion order).

Rather than relying on fragile automatic guessing, you can declare column sorting types explicitly:

```python
table = CTkTable(
    ...,
    sort_key={
        "default": "str",  # Standard alphabetical comparison
        0: "int",  # Column 0: Numeric comparison (1, 2, 10 instead of 1, 10, 2)
        1: "date",  # Column 1: Date comparison
        3: "float",  # Column 3: Numeric float comparison
    },
)
```
Supported types: `"str"`, `"int"`, `"float"`, `"date"`, or any custom function `Callable[[Any], Any]` (e.g. `sort_key={1: my_custom_key}`).

| Key | Sorting Behavior | Example Transformation | Fallback on Invalid/Empty |
| :--- | :--- | :--- | :--- |
| `"str"` *(default)* | Case-insensitive alphabetical order. | `"Alice"`, `"bob"` → `"alice"`, `"bob"` | `""` |
| `"int"` | Strips non-digit formatting and compares as whole numbers. | `"$1,420"`, `"-50kg"` → `1420`, `-50` (10 sorts after 2) | `0` |
| `"float"` | Strips currency and formatting symbols, compares as decimals. | `"£1,420.50"`, `"99.9%"` → `1420.50`, `99.9` | `0.0` |
| `"date"` | Chronological order for standard date strings (ISO format `YYYY-MM-DD`). | `"2026-03-15"` < `"2026-10-23"` | `""` |

#### Custom Sort Key Example
```python
# Sort priority status logically ("Critical" > "High" > "Medium" > "Low") instead of alphabetically:
PRIORITY = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}


def my_custom_key(val: str) -> int:
    return PRIORITY.get(val, -1)


table = CTkTable(
    app,
    headers=["Task", "Priority"],
    values=tasks,
    sort_key={1: my_custom_key},
)
```

### Sorting API in Code
```python
# Sort column 2 descending:
table.sort_by(2, ascending=False)

# Restore original baseline order (unless baked with commit_sort):
table.clear_sort()

# Or permanently bake the current sorted order into the raw data:
table.commit_sort()  # Sort arrows clear, this becomes the new baseline dataset

# Check what is currently sorted:
col, is_asc = table.get_sort_state()  # e.g., (None, True) after commit_sort
```

> **Zero Data Reshuffling:** Sorting never rearranges or copies the raw 50,000-row list. It only sorts an internal list of row numbers. Sorting takes ~15 milliseconds and never consumes extra memory.

---

## 7. In-Place Cell Editing

### How to Edit
* **Double-Click** any cell to edit it.
* Alternatively, select a cell and press **`Enter`**.

A floating entry box will appear directly over the cell:
* **`Enter`**: Saves the new value directly to the dataset, updates the display in place (no jump), and closes the input.
* **`Escape`**: Discards all changes and closes the input.
* **Clicking away (`FocusOut`)**: Automatically commits and closes.

### Binding Custom Keys (e.g. Enabling `F2` to Edit)
By default, `CTkTable` does not hijack function keys (`F1`–`F12`) so they remain free for your application's global hotkeys. 

If you want `F2` to trigger in-place editing on the active cell, simply hook it up in one line:

```python
# Enable F2 to edit the currently focused cell:
table.bind("<F2>", lambda _event: table.edit_focused_cell())
```

### Enabling & Restricting Editable Columns (`editable`)
By default, table cells are read-only (`editable=False`). You can enable editing globally or configure per-column rules using a single argument:

* **`editable=True`**: Entire table is editable.
* **`editable={"default": True, 0: False}`**: Entire table is editable, **except** column 0 (locked primary key).
* **`editable={1: True, 2: True}`**: Entire table is locked, **except** columns 1 and 2 (only they are editable).

```python
table = CTkTable(
    ...,
    editable={"default": True, 0: False},  # Edit all columns except ID
)
```

> **Baseline Preservation:** When reconfiguring with a dictionary (e.g. `table.configure(editable={3: False})`), omitting `"default"` preserves whatever baseline was already active.

### Listening for Edits (`on_cell_edit`)
Connect a callback to run code whenever a user modifies a cell:

```python
def handle_cell_edit(row_index, col_index, old_value, new_value):
    print(f"Row {row_index}, Col {col_index} changed from '{old_value}' to '{new_value}'")
    # You can trigger an auto-save or database update here


table = CTkTable(..., on_cell_edit=handle_cell_edit)
```

---

## 8. Clipboard Integration (`Ctrl + C`)

You can copy highlighted cells or rows to your system clipboard at any time:

* **Keyboard Shortcut**: Press **`Ctrl + C`** while focused on the table.
* **Format**: Standard Tab-Separated Values (TSV) with newlines. Pastes seamlessly into Excel, Google Sheets, LibreOffice, or plain text files.
* **In Code**: Call `table.copy_selection()`:
  ```python
  tsv_output = table.copy_selection()
  print("Copied to clipboard:", tsv_output)
  ```

---

## 9. Data CRUD Operations (Add, Delete, Update)

Manipulate records directly on live datasets with automatic sort-index mapping and coordinate synchronization:

### 1. Inserting Rows (`insert_row`)
```python
# Append a new row to the end of the table:
new_pos = table.insert_row(values=["105", "Grace Hopper", "5", "$300.00", "Completed"])

# Or insert at a specific row position:
table.insert_row(index=0, values=["100", "Ada Lovelace", "10", "$500.00", "Completed"])
```

### 2. Deleting Rows (`delete_rows`)
```python
# Delete a single row by index:
table.delete_rows(2)

# Or delete multiple rows in a batch (e.g., all currently selected rows):
selected = table.get_selected_rows()
table.delete_rows(selected)

# To delete selected rows with the Delete key, bind it explicitly:
table.bind("<Delete>", lambda _e: table.delete_rows(table.get_selected_rows()))
```

### 3. Updating Cells & Rows in Code (`update_cell`, `update_row`)
```python
# Modify a single cell in-place (row, col, new_value):
table.update_cell(0, 1, "Updated Customer Name")

# Modify an entire row atomically (display_row, new_values):
table.update_row(0, ["100", "Ada Lovelace", "12", "$600.00", "Verified"])
```

### 4. Mapping Between Visual and Raw Indexes (`get_raw_row_index`, `get_display_row_index`)

#### What is a Raw Index?
When rows are added to the table, each row receives a permanent number: its **raw index** (`0, 1, 2...`). This number never changes, no matter how many times you sort or scroll. If you ever need to know what index position a row held at creation before the table was sorted, its raw index tells you.


#### Practical Example
In real applications, each row in the table usually shows only a fraction of your data. For example, the table might display only a song's **Title** and **Size**, while your Python code holds the actual list of **MP3 audio files**:

```python
my_mp3_files = [song_a, song_b, song_c]  # Raw index 0, 1, 2
```

The **raw index** is the permanent connection between each MP3 file and its metadata row in the table.

When a user sorts the table (e.g. by Size), the rows on screen get shuffled into a new visual order. The only way to match a visual row back to its real MP3 file is with **`get_raw_row_index()`**:

```python
# Pass a single visual row index:
raw_row_index = table.get_raw_row_index(disp_row_index)
current_song = my_mp3_files[raw_row_index]

# Or pass a list of visual row indexes:
raw_row_indexes = table.get_raw_row_index(selected_rows)
```

#### Translating in Reverse
If you know the raw index of an MP3 file (e.g. `2`) and want to find where it is currently displayed on screen after sorting:

```python
disp_row_index = table.get_display_row_index(2)
table.select_row(disp_row_index)
table.scroll_to(row=disp_row_index)
```

### 5. Reading & Exporting Records (`get`, `get_row`, `get_cell`)
```python
# Export the full dataset in current visual sorted order (ideal for CSV/Excel export):
all_visible_data = table.get()

# Get all column values for a specific visual row:
record = table.get_row(0)  # or table.get(row=0)

# Get a single visual cell value:
customer_name = table.get_cell(row_index=0, col_index=1)  # or table.get(0, 1)

# Inspect raw unsorted baseline dataset:
raw_original_data = table.cget("values")
```

---

## 10. Row Styling (Uniform Flat vs Zebra Striping)

By default, all table rows inherit the parent container's `fg_color` (clean uniform flat look).

### 1. Opt-in Zebra Striping
If you prefer alternating row stripes, pass `alternate_row_color`:
```python
table = CTkTable(
    app,
    ...,
    alternate_row_color=("gray93", "gray14"),  # (light_mode_color, dark_mode_color)
)
```

### 2. Custom Base Row Color
You can also customize the primary row background color using `row_color`:
```python
table = CTkTable(
    app,
    ...,
    row_color=("#ffffff", "#1e1e1e"),
    alternate_row_color=("#f5f5f5", "#252525"),
)
```

---

## 11. Column & Header Styling (Single Polymorphic Arguments)

You can style text alignment, colors, and fonts across columns and headers using single arguments (`justify`, `text_color`, `font`, `header_alignment`, `header_text_color`, `header_font`).

Every styling argument accepts:
1. **A single value** (applies across all columns/headers).
2. **A dictionary with column index overrides and an optional `"default"` baseline**.

> **Automatic Fallback:** Whenever `"default"` is omitted from the dictionary, unlisted columns automatically use their normal theme defaults (e.g. standard theme font, theme label text color, `"left"` alignment).

### Text Alignment
```python
table = CTkTable(
    app,
    headers=["ID", "Name", "Department", "Salary", "Status"],
    values=data,
    # Body cell alignment (center ID and Status, right-align Salary, others default to left):
    justify={
        "default": "left",
        0: "center",
        3: "right",
        4: "center",
    },
    # Center all column header titles:
    header_alignment="center",
)
```

### Column & Header Text Colors
Pass hex strings or `(light_mode, dark_mode)` tuples:
```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    # Style specific body columns by index; unlisted columns use theme text color:
    text_color={
        3: ("#1b7a37", "#2ecc71"),  # Green: (light mode, dark mode) for column index 3
        4: ("#8a6d00", "#f1c40f"),  # Amber: (light mode, dark mode) for column index 4
    },
    # Set header baseline color and override column index 3:
    header_text_color={
        "default": "#3B8ED0",  # Baseline for all headers
        3: "#E06C75",  # Header column index 3 override
    },
)
```

### Fonts & Typography Shortcuts
Pass font tuples `("Family", size, "weight")`, `ctk.CTkFont` objects, or plain string shortcuts (`"bold"`, `"italic"`, `"bold italic"`):
```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    # Make column index 3 bold using a shortcut string:
    font={
        3: "bold",
    },
    # Custom font on header column index 3:
    header_font={
        3: ("Segoe UI", 13, "bold"),
    },
)
```

### Header Hover Tint
Highlight sortable column headers when hovered with `header_hover_color`:
```python
table = CTkTable(
    app,
    headers=headers,
    values=data,
    header_hover_color=("#3a7ebf", "#1f538d"),
)
```

---

## 12. Keyboard & Mouse Shortcuts Reference

| Action / Shortcut | Event | Description |
| :--- | :--- | :--- |
| **`Up` / `Down`** | `<Up>`, `<Down>` | Move active focus up or down by 1 row. |
| **`Left` / `Right`** | `<Left>`, `<Right>` | Move active focus across columns (in Cell mode). |
| **`PageUp` / `PageDown`** | `<Prior>`, `<Next>` | Jump up or down by one visible page of rows. |
| **`Home` / `End`** | `<Home>`, `<End>` | Jump straight to the first or last row. |
| **`Space`** | `<space>` | Toggle selection on the currently highlighted cell/row. |
| **`Enter`** | `<Return>` | Open in-place editor on focused cell (or commit active edit). |
| **`Escape`** | `<Escape>` | Deselect all highlighted items (or cancel active edit). |
| **`Ctrl + C`** | `<Control-c>` | Copy selected rows/cells to system clipboard as TSV (when `copyable=True`). |
| **`Ctrl + A`** | `<Control-a>` | Select all rows or cells in the table. |
| **`Click` (Header)** | `<Button-1>` | Cycle column sort: Ascending (▲), Descending (▼), Natural. |
| **`Drag` (Header Divider)** | `<B1-Motion>` | Interactively drag to resize column width. |
| **`Double-Click` (Header Divider)**| `<Double-Button-1>` | Auto-fit column width to content. |
| **`Mouse Wheel`** | `<MouseWheel>` | Vertical viewport scroll. |
| **`Shift + Mouse Wheel`** | `<Shift-MouseWheel>` | Horizontal viewport scroll. |

---

## 13. Complete Copy-Paste Example

```python
import customtkinter as ctk
from ctkforge.table import CTkTable

app = ctk.CTk()
app.geometry("950x560")

headers = ["ID", "Customer Name", "Quantity", "Price", "Status"]
data = [
    ["101", "Emma Watson", "4", "$120.00", "Shipped"],
    ["102", "Liam Neeson", "1", "$450.00", "Pending"],
    ["103", "Olivia Colman", "12", "$85.50", "Completed"],
    ["104", "James Bond", "2", "$950.00", "Shipped"],
]


def on_edit(row, col, old_val, new_val):
    print(f"Record #{row + 1} Col {col} edited: '{old_val}' -> '{new_val}'")


table = CTkTable(
    app,
    headers=headers,
    values=data,
    column_widths=[90, 200, 100, 120, 130],
    sort_key={"default": "str", 0: "int", 2: "int", 3: "float"},  # Numeric sorting on ID, Qty, and Price
    # Unified column alignment and styling:
    justify={"default": "left", 0: "center", 2: "center", 3: "right", 4: "center"},
    font={3: "bold"},
    text_color={3: ("#1b7a37", "#2ecc71")},  # Emerald highlight on Price
    header_alignment="center",
    header_hover_color=("#3a7ebf", "#1f538d"),
    editable={1: True, 2: True, 3: True},  # Only allow editing Name, Qty, Price
    on_cell_edit=on_edit,
    selection_target="row",
    selection_mode="extended",
    row_height=30,
    header_height=34,
)
table.pack(fill="both", expand=True, padx=20, pady=20)

app.mainloop()
```
