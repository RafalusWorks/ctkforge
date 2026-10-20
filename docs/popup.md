# CTkPopup API Reference & Documentation

A modern, DPI-aware modal dialog and alert popup for CustomTkinter with semantic button roles, automatic scrolling for long messages, and preset themes.

![CTkPopup Preview](assets/popup_preview.png)

---

## Table of Contents
1. [Quick Import & Initialization](#1-quick-import--initialization)
2. [Arguments (`__init__`)](#2-arguments-__init__)
   - [Container & Dimensions](#container--dimensions)
   - [Content & Presets](#content--presets)
   - [Button Configuration](#button-configuration)
   - [Appearance & Typography](#appearance--typography)
   - [Interaction & Lifecycle](#interaction--lifecycle)
3. [Methods](#3-methods)
4. [Class Attributes](#4-class-attributes)

---

## 1. Quick Import & Initialization

```python
import customtkinter as ctk

from ctkforge import CTkPopup

app = ctk.CTk()
app.geometry("400x240")
app.title("CTkPopup Demo")


def show_confirm() -> None:
    popup = CTkPopup(
        master=app,
        title="Confirm Deletion",
        message="Are you sure you want to delete this record? This action cannot be undone.",
        preset="warning",
        buttons=[
            {"label": "Delete", "value": True, "role": "destructive"},
            {"label": "Cancel", "value": False, "role": "cancel"},
        ],
    )
    choice = popup.get()
    print(f"User choice: {choice}")


btn = ctk.CTkButton(app, text="Delete Item", command=show_confirm)
btn.pack(expand=True)

app.mainloop()
```

---

## 2. Arguments (`__init__`)

### Container & Dimensions

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `master` | `Any` | `None` | Parent window or frame (e.g. `CTk`, `CTkToplevel`, or `CTkFrame`). Automatically centers dialog over master. |
| `width` | `int` | `478` | Target dialog width in logical pixels. |
| `wraplength` | `int` | `340` | Maximum horizontal wrap boundary for message text in logical pixels. |
| `max_label_height` | `int` | `300` | Height threshold in logical pixels before auto-switching message display into a scrollable, copyable `CTkTextbox`. |

### Content & Presets

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` | `str \| None` | `None` | Window title bar text. Falls back to preset title or `"Alert"` when omitted. |
| `text` | `str` | `""` | Message text, confirmation prompt, or exception traceback to display. |
| `icon` | `ctk.CTkImage \| str \| Path \| None` | `None` | Stock preset name (`"info"`, `"warning"`, `"error"`, `"question"`, `"success"`), custom image file path, or `CTkImage`. |
| `preset` | `str \| None` | `None` | Predefined template (`"info"`, `"warning"`, `"error"`, `"question"`, `"success"`) configuring default title, icon, and button actions. |

### Button Configuration

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `buttons` | `list[str \| tuple \| dict] \| None` | `None` | Custom button definitions. Accepts strings (`["OK"]`), tuples (`[("Save", True, "primary")]`), or dicts (`[{"label": "OK", "value": "ok", "role": "primary"}]`). |
| `default_button` | `Any` | `_SENTINEL` | Value returned when pressing `<Return>`. Defaults to preset primary button value. |
| `cancel_button` | `Any` | `_SENTINEL` | Value returned when pressing `<Escape>` or clicking the window close (`X`) button. Defaults to preset cancel button value. |

### Appearance & Typography

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `corner_radius` | `int` | `12` | Corner curvature of the popup frame in logical pixels. |
| `border_width` | `int` | `1` | Frame border thickness in logical pixels. |
| `border_color` | `str \| tuple[str, str]` | `("gray80", "gray25")` | Frame border color or light/dark tuple. |
| `fg_color` | `str \| tuple[str, str] \| None` | `None` | Background fill color for the inner card. |
| `text_color` | `str \| tuple[str, str] \| None` | `None` | Message text color or light/dark tuple. |
| `font` | `tuple[str, int] \| CTkFont \| None` | `None` | Font used for message text. Defaults to `CTkFont(size=13)`. Long tracebacks automatically use Consolas. |

### Interaction & Lifecycle

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `callback` | `Callable[[Any], None] \| None` | `None` | Optional non-blocking callback executed with user choice upon dialog dismissal: `def on_choice(result): ...` |
| `sound` | `bool` | `False` | When `True`, triggers the system audio bell upon dialog reveal. |

---

## 3. Methods

All options can be updated dynamically via `.configure()` and queried via `.cget()`.

### Configuration & Inspection

#### `.configure(**kwargs) -> None`
Dynamically updates text, titles, presets, icons, styling tokens, or buttons live.
```python
popup.configure(text="Operation succeeded!", border_color="#10B981")
```

#### `.cget(attribute_name: str) -> Any`
Reads active settings (`"text"`, `"title"`, `"icon"`, `"border_width"`, etc.).
```python
msg = popup.cget("text")
```

---

### Dialog Lifecycle & Retrieval

#### `.get() -> Any`
Synchronously waits for user action, releases window grab, closes the dialog, and returns the selected value.
```python
choice = popup.get()
```


---

## 4. Class Attributes

```python
# Standard preset templates (title, icon, buttons, keyboard defaults):
presets = CTkPopup.PRESETS

# Semantic button role color palettes ('primary', 'destructive', 'cancel', 'normal'):
role_colors = CTkPopup.ROLE_COLORS
```
