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

---

## 6. Header Column Sorting

### How to Sort
Click any column header to cycle through three states:
1. **1st Click**: Sorts **Ascending** (indicated by `▲`).
2. **2nd Click**: Sorts **Descending** (indicated by `▼`).
3. **3rd Click**: **Clears Sort** (instantly restores original database order).

### Enabling & Restricting Header Sorting (`header_sortable` & `header_sortable_exclude`)

By default, users can click any column header to sort. You can toggle interactive sorting globally and declare specific columns as exceptions using `header_sortable` and `header_sortable_exclude`:

```python
table = CTkTable(
    ...,
    header_sortable=True,             # Base rule: True (all on) or False (all off)
    header_sortable_exclude=[3, 4],   # Column numbers inverted from the base rule
)
```

#### How It Works

| `header_sortable` | `header_sortable_exclude` | What Happens on Header Click |
| :--- | :--- | :--- |
| **`True`** (default) | `None` (default) | **All columns sortable.** Clicking any column header cycles its sort. |
| **`True`** | `[3, 4]` | **All columns sortable except [3, 4].** Clicking column 3 or 4 is ignored; all other columns sort normally. |
| **`False`** | `None` | **Total lock.** Clicking any column header is ignored. |
| **`False`** | `[3, 4]` | **All columns locked except [3, 4].** Only columns 3 and 4 can be sorted by clicking. |

> **Programmatic Sorting Always Allowed:** Disabling header clicks only blocks interactive mouse clicks. You can still sort any column programmatically from Python code via `table.sort_by(...)` at any time.

### Explicit Column Types (`column_types`)
Rather than relying on fragile automatic guessing, you can declare column types explicitly:

```python
table = CTkTable(
    ...,
    column_types={
        0: "int",      # Column 0: Numeric comparison (1, 2, 10 instead of 1, 10, 2)
        1: "date",     # Column 1: Date comparison
        2: "str",      # Column 2: Standard alphabetical comparison
    }
)
```
Supported types: `"int"`, `"float"`, `"str"`, and `"date"`.

### Custom Sort Keys (`column_sort_keys`)
When a column contains special formatting (like currencies or file sizes), pass a custom extractor:

```python
def parse_currency(val):
    # Extracts numeric float from "$1,420.50" -> 1420.50
    cleaned = "".join(ch for ch in str(val) if ch.isdigit() or ch in ".-")
    return float(cleaned) if cleaned else 0.0

table = CTkTable(
    ...,
    column_sort_keys={
        3: parse_currency,  # Column 3: Custom currency sorting
    }
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

### Enabling & Restricting Editable Columns (`editable` & `editable_columns_exclude`)
By default, table cells are read-only (`editable=False`). This follows the exact same base-rule and exception logic as [Header Column Sorting](#enabling--restricting-header-sorting-header_sortable--header_sortable_exclude):
* **`editable=False, editable_columns_exclude=[1, 2]`**: Entire table is locked, **except** columns 1 and 2 (only they are editable).
* **`editable=True, editable_columns_exclude=[0]`**: Entire table is editable, **except** column 0 (locked primary key).

```python
table = CTkTable(
    ...,
    editable=False,                   # Base rule: False (all locked) or True (all editable)
    editable_columns_exclude=[1, 2],  # Column numbers inverted from the base rule
)
```

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

### 3. Updating a Cell in Code (`update_cell`)
```python
# Modify a single cell in-place (row, col, new_value):
table.update_cell(0, 1, "Updated Customer Name")
```

### 4. Reading & Exporting Records (`get`, `get_row`, `get_cell`)
```python
# Export the full dataset in current visual sorted order (ideal for CSV/Excel export):
all_visible_data = table.get()

# Get all column values for a specific visual row:
record = table.get_row(0)      # or table.get(row=0)

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

## 11. Keyboard & Mouse Shortcuts Reference

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

## 12. Complete Copy-Paste Example

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

def parse_price(val):
    cleaned = "".join(ch for ch in str(val) if ch.isdigit() or ch in ".-")
    return float(cleaned) if cleaned else 0.0

def on_edit(row, col, old_val, new_val):
    print(f"Record #{row + 1} Col {col} edited: '{old_val}' -> '{new_val}'")

table = CTkTable(
    app,
    headers=headers,
    values=data,
    column_widths=[90, 200, 100, 120, 130],
    column_types={0: "int", 2: "int"},       # Numeric sorting on ID and Qty
    column_sort_keys={3: parse_price},        # Custom currency sorting on Price
    editable=False,
    editable_columns_exclude=[1, 2, 3],       # Only allow editing Name, Qty, Price
    on_cell_edit=on_edit,
    selection_target="row",
    selection_mode="extended",
    row_height=30,
    header_height=34,
)
table.pack(fill="both", expand=True, padx=20, pady=20)

app.mainloop()
```
