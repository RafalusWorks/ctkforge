# CTkForge

Custom extension components and widgets for [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

## Installation

```bash
pip install ctkforge
```

## Features

- **[CTkPopup](docs/CTkPopup.md)**: A modern popup dialog widget for alerts, confirmations, and error messages. Includes ready-to-use types (info, warning, error, question, success), keyboard shortcuts (Enter to confirm, Escape to cancel), clean Windows 11 button styling, and automatically turns into a scrollable box for long error text. See [detailed documentation](docs/CTkPopup.md) or run [example_ctkpopup.py](examples/example_ctkpopup.py).

- **[CTkSpinbox](docs/CTkSpinbox.md)**: A number input widget with classic up and down arrow buttons (`▲`/`▼`). Supports mouse wheel scrolling, arrow key adjustments, minimum/maximum limits, custom steps, and matches CustomTkinter's colors and rounded corners. See [detailed documentation](docs/CTkSpinbox.md) or run [example_ctkspinbox.py](examples/example_ctkspinbox.py).

- **[CTkTable](docs/table.md)**: A fast, smooth data table widget built to handle massive datasets without slowing down. Features smart column sorting, row and cell selection, double-click cell editing, copy-pasting (`Ctrl+C`), auto-fitting column widths, and optional alternating row colors. See [API reference](docs/table.md), [user guide](docs/table_user_guide.md), or run [demo_ctktable_basic.py](examples/demo_ctktable_basic.py).
- **Universal DPI `unscale` Helper**: Utility function to convert raw physical pixel dimensions from Tkinter (`winfo_*`) back to unscaled 100% baseline (96 DPI) values for CustomTkinter windows.
- **Resource Locator (`resource_path`)**: Robust asset path resolver that finds images, icons, audio, and data files across direct filesystem paths, the script entry directory (`sys.argv[0]`), and PyInstaller single-file bundle extractions (`sys._MEIPASS`).

## Usage

### 1. CTkPopup Dialogs

```python
import customtkinter as ctk
from ctkforge import CTkPopup

app = ctk.CTk()

# Quick confirmation dialog (Enter for Yes, Escape for No)
popup = CTkPopup(
    master=app,
    title="Confirm Action",
    message="Do you want to proceed with the update?",
    type="question",
)

choice = popup.get()
if choice is True:
    print("User clicked Yes")
else:
    print("User clicked No or closed the dialog")

app.mainloop()
```

*(See [example_ctkpopup.py](examples/example_ctkpopup.py) and [demo_ctkpopup.py](examples/demo_ctkpopup.py) for interactive demos).*

### 2. CTkSpinbox

```python
import customtkinter as ctk
from ctkforge import CTkSpinbox

app = ctk.CTk()

spinbox = CTkSpinbox(
    app,
    start_value=25,
    min_value=1,
    max_value=100,
    step=1,
    width=120,
    height=38,
)
spinbox.pack(padx=20, pady=20)

app.mainloop()
```

*(See [example_ctkspinbox.py](examples/example_ctkspinbox.py) for the standalone snippet, and [demo_ctkspinbox.py](examples/demo_ctkspinbox.py) for a complete app).*

### 3. CTkTable Data Grid

```python
import customtkinter as ctk
from ctkforge import CTkTable

app = ctk.CTk()
app.geometry("800x400")

headers = ["ID", "Employee Name", "Department", "Salary"]
data = [
    ["101", "Ada Lovelace", "Research", "$125,000"],
    ["102", "Alan Turing", "Data Systems", "$135,000"],
    ["103", "Grace Hopper", "Engineering", "$130,000"],
]

table = CTkTable(
    app,
    headers=headers,
    values=data,
    column_widths=[90, 220, 180, 140],
    column_types={0: "int"},
    selection_target="row",
    selection_mode="extended",
    editable=True,
    alternate_row_color=("gray92", "gray14"),
)
table.pack(fill="both", expand=True, padx=20, pady=20)

app.mainloop()
```

*(See [example_ctktable.py](examples/example_ctktable.py), [demo_ctktable_basic.py](examples/demo_ctktable_basic.py), and [demo_ctktable_clipboard_and_crud.py](examples/demo_ctktable_clipboard_and_crud.py) for interactive demos).*

### 4. Universal DPI Unscaling (`unscale`)

Convert raw physical pixel values from Tkinter (`winfo_*`) back to unscaled 100% baseline (96 DPI) values to prevent double-scaling bugs when setting CustomTkinter geometry on High-DPI displays:

```python
import customtkinter as ctk
from ctkforge import unscale

app = ctk.CTk()
app.update_idletasks()

# Unscale multiple physical dimensions simultaneously:
width, height = unscale(app, app.winfo_width(), app.winfo_height())

# Or unscale a single coordinate:
root_x = unscale(app, app.winfo_rootx())

# Set window geometry safely without High-DPI drift:
app.geometry(f"{width}x{height}")
```

### 5. Resource Path Resolution (`resource_path`)

Find files reliably in both development and PyInstaller single-file executables (`.exe`):

```python
from ctkforge import resource_path

# Finds asset whether running from terminal, script folder, or PyInstaller bundle
icon_path = resource_path("assets/custom_icon.png")
```

