# CTkPopup User Guide

A modern, DPI-aware modal dialog and alert popup library for CustomTkinter.

---

## Table of Contents
1. [Quickstart](#1-quickstart)
2. [Presets](#2-presets)
3. [Button Customization](#3-button-customization)
4. [Keyboard Navigation & Dismissal](#4-keyboard-navigation--dismissal)
5. [Long Messages & Clipboard Copy](#5-long-messages--clipboard-copy)
6. [Synchronous vs Asynchronous Modes](#6-synchronous-vs-asynchronous-modes)
7. [Dynamic Configuration (.configure & .cget)](#7-dynamic-configuration-configure--cget)
8. [Icons](#8-icons)
9. [Localization & Global Theming](#9-localization--global-theming)

---

## 1. Quickstart

Pass `master=app` to center the popup modally over your application window, then call `.get()` to retrieve the result:

```python
import customtkinter as ctk
from ctkforge import CTkPopup

app = ctk.CTk()
app.geometry("400x200")

popup = CTkPopup(
    master=app,
    title="Confirm",
    text="Do you want to proceed with this operation?",
    preset="question",
)

if popup.get() == "yes":
    print("User confirmed.")
else:
    print("User cancelled.")

app.mainloop()
```

---

## 2. Presets

Presets preconfigure the title, stock icon, action buttons, and keyboard shortcuts:

| Preset | Title | Icon | Buttons | Return Values | `<Return>` | `<Escape>` / `X` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `info` | `"Information"` | `info` | `[ OK ]` | `"ok"` | `"ok"` | `"ok"` |
| `warning` | `"Warning"` | `warning` | `[ OK ]` `[ Cancel ]` | `"ok"`, `"cancel"` | `"ok"` | `"cancel"` |
| `error` | `"Error"` | `error` | `[ OK ]` *(red)* | `"ok"` | `"ok"` | `"ok"` |
| `question` | `"Confirm"` | `question` | `[ Yes ]` `[ No ]` | `"yes"`, `"no"` | `"yes"` | `"no"` |
| `success` | `"Success"` | `success` | `[ OK ]` | `"ok"` | `"ok"` | `"ok"` |

### Code Examples

```python
# 1. Information
CTkPopup(master=app, text="Export completed.", preset="info").get()

# 2. Warning
if CTkPopup(master=app, text="File exists. Overwrite?", preset="warning").get() == "ok":
    overwrite()

# 3. Error
CTkPopup(master=app, text="Connection timed out.", preset="error").get()

# 4. Question
if CTkPopup(master=app, text="Save before closing?", preset="question").get() == "yes":
    save()

# 5. Success
CTkPopup(master=app, text="Record saved successfully.", preset="success").get()
```

### Omitted Preset (`preset=None`)
When `preset` is omitted, `CTkPopup` renders a clean alert with no icon and a single `[ OK ]` button returning `"ok"`:

```python
result = CTkPopup(master=app, text="System maintenance scheduled for midnight.").get()
# Returns "ok"
```

---

## 3. Button Customization

Custom buttons can be supplied via plain strings, tuples, or full dictionaries:

### Method A: Plain Strings
```python
# First button becomes primary (<Return>); last button becomes cancel (<Escape>)
choice = CTkPopup(
    master=app,
    text="Choose action:",
    buttons=["Save", "Discard", "Cancel"],
).get()
# Returns "Save", "Discard", or "Cancel"
```

### Method B: Tuples `(text, value, [role])`
```python
# Explicit return tokens and roles
resolution = CTkPopup(
    master=app,
    text="Select resolution:",
    buttons=[
        ("High (1080p)", 1080),
        ("Ultra 4K", 2160, "primary"),
        ("Cancel", 0, "cancel"),
    ],
).get()
# Returns 1080, 2160, or 0
```

### Method C: Full Dictionaries
```python
action = CTkPopup(
    master=app,
    text="Manage existing file:",
    icon="warning",
    buttons=[
        {"text": "Keep Both", "value": "rename", "role": "primary"},
        {"text": "Overwrite", "value": "overwrite", "role": "destructive"},
        {"text": "Cancel", "value": "cancel", "role": "cancel"},
    ],
).get()
# Returns "rename", "overwrite", or "cancel"
```

### Supported Roles
* `"primary"`: Active CustomTkinter theme accent color. Bound to `<Return>`.
* `"destructive"`: Danger red. Requires explicit mouse click.
* `"cancel"`: Soft muted gray. Bound to `<Escape>` and window `X`.
* `"normal"`: Secondary neutral gray.

For custom color overrides per button (`fg_color`, `hover_color`, `text_color`), see the [Button Dictionary Specification](popup.md#button-dictionary-specification).

---

## 4. Keyboard Navigation & Dismissal

* **`<Return>`**: Activates the primary button (or explicitly configured `default_button`).
* **`<Escape>` & Window `X`**: Activates the cancel button (or explicitly configured `cancel_button`).

### Custom Key Mappings
```python
popup = CTkPopup(
    master=app,
    text="Launch rocket?",
    buttons=["Launch", "Abort"],
    default_button="Launch",  # Bound to <Return>
    cancel_button="Abort",   # Bound to <Escape> and window close 'X'
)
```

---

## 5. Long Messages & Clipboard Copy

Messages exceeding 300 vertical pixels (`max_label_height`) automatically switch from a `CTkLabel` to a scrollable `CTkTextbox`. Users can select text with the mouse and press `Ctrl+C` to copy error tracebacks or stack dumps. Action buttons remain pinned at the bottom.

---

## 6. Synchronous vs Asynchronous Modes

### Synchronous Mode (Default)
Halts caller execution modally until the user interacts:
```python
choice = CTkPopup(master=app, text="Proceed?", preset="question").get()
if choice == "yes":
    proceed()
```

### Asynchronous Mode (`callback=...`)
Runs non-blockingly without halting the calling thread:
```python
def on_dismiss(choice: str) -> None:
    print(f"User chose: {choice}")


CTkPopup(
    master=app,
    text="Operation in progress...",
    buttons=["Stop", "Dismiss"],
    callback=on_dismiss,
)
# Execution continues immediately to the next statement
```

---

## 7. Dynamic Configuration (`.configure` & `.cget`)

All properties can be inspected via `.cget()` and modified dynamically via `.configure()`:

```python
popup = CTkPopup(master=app, text="Uploading...", title="Status", preset="info")

# Read active property
current_text = popup.cget("text")
current_preset = popup.cget("preset")

# Dynamically update live popup
popup.configure(
    text="Upload complete!",
    title="Finished",
    preset="success",
    buttons=["OK"],
)
```

---

## 8. Icons

Icons are resolved through three sources:

### 1. Stock Keyword
Pass any of the 5 built-in names: `"info"`, `"warning"`, `"error"`, `"question"`, `"success"`.
```python
CTkPopup(master=app, text="Done.", icon="success").get()
```

### 2. Image File Path
Pass a `Path` or path string to a `.png`, `.ico`, or `.jpg` file. Paths resolve across normal runs and PyInstaller frozen executables.
```python
CTkPopup(master=app, text="Custom Branding", icon="assets/logo.png").get()
```
> If a custom icon path cannot be found, a warning is printed to `sys.stderr` and the preset stock icon is displayed as a fallback.

### 3. Pre-configured `ctk.CTkImage`
Pass a `ctk.CTkImage` directly when distinct Light and Dark mode assets are needed:
```python
from PIL import Image
import customtkinter as ctk
from ctkforge import CTkPopup, resource_path

custom_icon = ctk.CTkImage(
    light_image=Image.open(resource_path("assets/icon_dark.png")),
    dark_image=Image.open(resource_path("assets/icon_light.png")),
    size=(64, 64),
)
CTkPopup(master=app, text="Theme-aware icon", icon=custom_icon).get()
```

---

## 9. Localization & Global Theming

`PRESETS` and `ROLE_COLORS` can be customized globally at application startup:

### Translating Preset Defaults
```python
from ctkforge import CTkPopup

# Rebrand the Question preset to French across the entire application
CTkPopup.PRESETS["question"] = {
    "title": "Confirmation",
    "icon": "question",
    "buttons": [
        {"text": "Oui", "value": "oui", "role": "primary"},
        {"text": "Non", "value": "non", "role": "cancel"},
    ],
    "default_button": "oui",
    "cancel_button": "non",
}
```

### Changing Role Colors
```python
# Override destructive red across all popups
CTkPopup.ROLE_COLORS["destructive"] = {
    "fg_color": ("#E65100", "#FF6D00"),
    "hover_color": ("#BF360C", "#DD2C00"),
    "text_color": ("#FFFFFF", "#FFFFFF"),
}
```
