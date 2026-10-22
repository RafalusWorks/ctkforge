# Utilities

Utility functions for High-DPI coordinate calculations and cross-environment asset resolution.

## 1. Universal DPI Unscaling (`unscale`)

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

## 2. Resource Path Resolution (`resource_path`)

Find files reliably in both development and PyInstaller single-file executables (`.exe`):

```python
from ctkforge import resource_path

# Finds asset whether running from terminal, script folder, or PyInstaller bundle
icon_path = resource_path("assets/custom_icon.png")
```
