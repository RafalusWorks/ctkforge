# CTkPopup User Guide

A modern, reliable, and DPI-aware popup dialog library for **CustomTkinter**.

---

## Table of Contents
1. [What is CTkPopup?](#what-is-ctkpopup)
2. [Basic Integration](#2-basic-integration)
3. [API & Parameters Reference](#3-api--parameters-reference)
4. [Quickstart (The Single Habit)](#quickstart-the-single-habit)
5. [The 5 Core Presets (`preset="..."`)](#5-the-5-core-presets-preset)
6. [Customizing Buttons & Semantic Roles](#6-customizing-buttons--semantic-roles)
7. [Keyboard Controls (Enter & Escape)](#keyboard-controls-enter--escape)
8. [Long Messages & Error Copying (Ctrl+C)](#long-messages--error-copying-ctrlc)
9. [Synchronous vs Asynchronous (Callbacks)](#synchronous-vs-asynchronous-callbacks)
10. [CustomTkinter Dynamic Configuration (.configure & .cget)](#10-customtkinter-dynamic-configuration-configure--cget)
11. [Icons & Smart Fallbacks](#11-icons--smart-fallbacks)
12. [Global Rebranding & Localization](#global-rebranding--localization)

---

## 1. What is CTkPopup?

`CTkPopup` is a modern, theme-aware dialog and popup window system built specifically for **CustomTkinter**. It seamlessly matches your application's light or dark mode while delivering a rock-solid, production-grade feature set:

* **Seamless Theming:** Automatically adapts to CustomTkinter's appearance modes (`"dark"`, `"light"`) and active color themes.
* **Semantic Button Roles:** Dedicated resting and hover colors for `primary` (theme accent), `destructive` (warning red), `cancel` (muted gray), and `normal` actions.
* **Flexible Button Layouts:** Renders any button count without distortion using plain strings, compact tuples, or full dictionaries.
* **Decoupled Semantic Values:** Return clean standardized tokens (e.g. `"ok"`, `"cancel"`), independent of display text or language localization.
* **DPI-Aware Geometry:** Hidden-staging coordinates guarantee the popup spawns centered over its parent window without visible screen jumping or flickering on high-DPI (4K) monitors.
* **Smart Text Layouts:** Displays short messages in lightweight labels, and automatically switches long tracebacks or logs to a scrollable `CTkTextbox` with full mouse selection and `Ctrl+C` clipboard support.
* **Keyboard Ergonomics:** `<Return>` triggers the primary action; `<Escape>` and the window close "X" safely trigger cancellation.
* **Synchronous & Asynchronous:** Supports standard modal blocking (`.get()`) as well as non-blocking background callbacks (`callback=...`).
* **High-DPI Master Assets:** Bundled with crisp 256×256 master PNG assets downsampled via Lanczos filtering for razor-sharp rendering on Retina/4K displays.

---

## 2. Basic Integration

When embedding inside a CustomTkinter GUI, always pass `master=app`. This ensures the popup attaches modally and centers directly over your application window:

```python
import customtkinter as ctk
from ctkforge import CTkPopup

app = ctk.CTk()

# Providing master=app centers the popup over your app
CTkPopup(master=app, text="Task completed successfully!").get()

app.mainloop()
```

---

## 3. API & Parameters Reference

`CTkPopup` is built strictly as a true CustomTkinter citizen: all visual and functional attributes follow CustomTkinter naming conventions (e.g. `text` rather than `message`), and runtime inspection and mutation are managed through standard `.cget()` and `.configure()` methods.

> [!NOTE]
> For the comprehensive, formal parameter reference tables, types, and defaults, see the **[CTkPopup API Reference](popup.md#2-arguments-__init__)**.

### Key Methods at a Glance

| Method | Syntax | What it does |
| :--- | :--- | :--- |
| **`.get()`** | `result = popup.get()` | Modally halts execution and returns the clicked button's value. |
| **`.cget()`** | `val = popup.cget("text")` | Reads any active configuration property (`text`, `title`, `preset`, etc.). |
| **`.configure()`** | `popup.configure(text="...", preset="error")` | Dynamically updates text, titles, presets, or buttons live on screen. |

---

## 4. Quickstart (The Single Habit)

Import `CTkPopup`, create the dialog, and call `.get()`:

```python
import customtkinter as ctk
from ctkforge import CTkPopup

app = ctk.CTk()

# 1. Create the dialog widget
popup = CTkPopup(
    master=app,
    title="Confirm",
    text="Do you want to proceed?",
    preset="question",
)

# 2. Read the user's choice
if popup.get() is True:
    print("User clicked Yes!")
else:
    print("User clicked No or closed the window.")

app.mainloop()
```
---

## 5. The 5 Core Presets (`preset="..."`)

### What Are Presets?
Presets are ready-to-use templates for the five most common dialog scenarios in software development: **Information**, **Warning**, **Error**, **Question**, and **Success**.

### Why Use Them? (The Developer Advantage)
Instead of manually writing code to configure six separate things every time you need a simple dialog:

```python
# The manual boilerplate (configuring everything by hand)
popup = CTkPopup(
    master=app,
    title="Low Disk Space",  # 1. Setting a window title
    text="You have less than 1 GB remaining.",  # 2. Message text
    icon="assets/warning.png",  # 3. Finding and loading an icon image
    # Writing button labels, seting value, role
    buttons=[
        {"text": "Proceed", "value": True, "role": "primary"},
        {"text": "Cancel", "value": False, "role": "cancel"},
    ],
    default_button=True,  # 6. Binding <Return> and <Escape> keys
    cancel_button=False,
)
```

You pass a single keyword: `preset="..."`:

```python
# The preset way (one keyword replaces all manual boilerplate)
popup = CTkPopup(
    master=app,
    title="Low Disk Space",
    text="You have less than 1 GB remaining.",
    preset="warning",
)
```

* **Zero Boilerplate:** Instead of writing the 12 lines of manual setup seen in the first code block, passing `preset="warning"` in the second code block configures the warning icon, default title, Proceed/Cancel buttons, role colors, and Enter/Escape keybindings in one clean call.
* **App-Wide Consistency:** Guarantees that every warning, confirmation, and error across your entire codebase has the exact same look, feel, and keyboard behavior without copy-pasting code blocks.
* **Fully Overridable:** Presets provide sensible defaults for free, but you can still override any single property (e.g. supply your own custom `title="Database Alert"`) without breaking the rest of the template.

---

### 1. Information (`preset="info"`)
Shows a blue informational badge with an **OK** button. Returns `"ok"`.
```python
result = CTkPopup(
    master=app,
    title="Update Available",
    text="Version 2.0 has been downloaded.",
    preset="info",
).get()
# result is "ok"
```

### 2. Warning (`preset="warning"`)
Shows an amber warning triangle with **OK** and **Cancel** buttons. Returns `"ok"` or `"cancel"`.
```python
popup = CTkPopup(
    master=app,
    title="Low Disk Space",
    text="You have less than 1 GB remaining. Continue?",
    preset="warning",
)
if popup.get() == "ok":
    continue_download()
```

### 3. Error (`preset="error"`)
Shows a red error badge with an **OK** button styled in danger red. Returns `"ok"`.
```python
CTkPopup(
    master=app,
    title="Connection Failed",
    text="Unable to reach database server.",
    preset="error",
).get()
```

### 4. Question (`preset="question"`)
Shows an indigo question mark with **Yes** and **No** buttons. Returns `"yes"` for affirmative and `"no"` for cancellation.
```python
popup = CTkPopup(
    master=app,
    title="Save Changes",
    text="Save changes before exiting?",
    preset="question",
)
if popup.get() == "yes":
    save_file()
```

### 5. Success (`preset="success"`)
Shows an emerald green checkmark with an **OK** button. Returns `"ok"`.
```python
CTkPopup(
    master=app,
    title="Complete",
    text="Your file was saved successfully.",
    preset="success",
).get()
```

### What If `preset` Is Omitted? (`preset=None`)

When `preset` is omitted (`preset=None`), **no preset is active**. `CTkPopup` falls back to a clean, generic **"Alert"** dialog:

| Feature | Fallback Behavior (When `preset=None`) |
| :--- | :--- |
| **Title** | Defaults to `"Alert"` (unless you pass custom `title="..."`). |
| **Icon** | `None` (no icon widget is rendered, giving the entire width to your message text). |
| **Buttons** | A single **`OK`** button styled in the primary theme color. |
| **Return Value** | Returns `"ok"` when clicked, or on `<Return>` (Enter) / `<Escape>` / window "X". |

#### Code Example: Without `preset`
```python
from ctkforge import CTkPopup

# The bare generic fallback
popup = CTkPopup(
    master=app,
    text="System maintenance scheduled for midnight.",
)
result = popup.get()
# Window title: "Alert"
# Icon: None
# Buttons: [OK] -> returns "ok"
```

#### Smart Convenience Feature
If you forget `preset="warning"` but pass `icon="warning"`:
```python
popup = CTkPopup(master=app, text="Check this out", icon="warning")
```
`CTkPopup` automatically detects that `"warning"` is a valid preset name and activates the warning preset template for you.

---

## 6. Customizing Buttons & Semantic Roles

You do not need to stick to preset buttons. You can pass your own button list using strings, tuples, or full dictionaries:

### The 4 Button Roles & Colors

Every button has a semantic "role" that tells CustomTkinter how to color it:

| Role Name | What It Looks Like | What It Is For | Keyboard Shortcut |
| :--- | :--- | :--- | :--- |
| `"primary"` | Theme Accent (Blue, Green, etc.) | The main positive action (`Save`, `Submit`, `OK`) | Triggered by `<Return>` (Enter) |
| `"cancel"` | Muted Soft Gray | Safe exit or dismissal (`Cancel`, `Dismiss`) | Triggered by `<Escape>` & titlebar "X" |
| `"destructive"`| Warning Danger Red | Dangerous or irreversible actions (`Delete`, `Wipe`) | Never default; requires mouse click |
| `"normal"` | Neutral Gray / Secondary | Optional choices in 3+ button menus (`Later`, `Skip`) | None |

> **Hover Colors:** Unlike basic scripts where hovering turns red buttons blue, `CTkPopup` provides dedicated light and dark mode hover shades for every role (e.g. destructive red darkens into deep burgundy on hover).

> **Windows UX Button Order Standard (Microsoft Guidelines):**  
> To provide a native, predictable experience on Windows desktop applications:
> * **Primary / Affirmative actions come first (left):** `[ Proceed ]`, `[ Yes ]`, `[ Delete ]`, `[ Save ]`.
> * **Dismissive / Cancel actions come last (far right):** `[ Cancel ]`, `[ No ]`.
> 
> *(Windows users read left-to-right and expect the commit action first, with the safe escape option at the far right edge).*

### Method A: Plain String List (Zero Boilerplate)
If you pass simple strings, `CTkPopup` automatically assigns the first button as primary (Enter key), the last button as cancel (Escape key), and any middle buttons as neutral secondary gray (`"normal"`):

```python
from ctkforge import CTkPopup

popup = CTkPopup(
    master=app,
    title="File Conflict",
    text="A file named 'report.pdf' already exists:",
    buttons=["Keep Both", "Overwrite", "Cancel"],
)
choice = popup.get()
print("User chose:", choice)  # Returns "Keep Both", "Overwrite", or "Cancel"
```

### Method B: Compact Tuples (Label, Return Value, Role)
Tuples let you set what machine value gets returned:

```python
popup = CTkPopup(
    master=app,
    title="Select Quality",
    text="Choose export video resolution:",
    buttons=[
        ("High (1080p)", 1080),  # (label, return_value)
        ("Ultra 4K", 2160, "primary"),  # (label, return_value, role)
        ("Cancel", 0, "cancel"),
    ],
)
resolution = popup.get()  # Returns 1080, 2160, or 0
```

### Method C: Full Dictionaries (Total Control)
Use full dictionaries when you want explicit labels, custom return values, dedicated role colors, or custom styling:

```python
popup = CTkPopup(
    master=app,
    title="File Already Exists",
    text="A file named 'report.pdf' already exists in this folder. What would you like to do?",
    icon="warning",
    buttons=[
        {"text": "Keep Both", "value": "rename", "role": "primary"},
        {"text": "Overwrite", "value": "overwrite", "role": "destructive"},
        {"text": "Cancel", "value": False, "role": "cancel"},
    ],
)
action = popup.get()
# Returns "rename", "overwrite", or False
```

> **Tip:** Both `"text"` (standard CustomTkinter syntax) and `"label"` are supported. For the complete list of accepted dictionary keys (including custom button colors), see the [Button Dictionary Specification](popup.md#button-dictionary-specification).

---

## 7. Keyboard Controls (Enter & Escape)

`CTkPopup` is fully navigable by keyboard out of the box:
- Pressing **`<Return>` (Enter)** automatically clicks the primary button.
- Pressing **`<Escape>`** or clicking the window's **"X"** button safely triggers the cancel button.

You can also explicitly choose which values map to Enter and Escape:
```python
popup = CTkPopup(
    master=app,
    text="Press Enter to launch, or Escape to abort.",
    buttons=["Launch", "Abort"],
    default_button="Launch",  # Bound to <Return>
    cancel_button="Abort",  # Bound to <Escape> and the red 'X'
)
```

---

## 8. Long Messages & Error Copying (Ctrl+C)

In standard message boxes, long text is unreadable or pushes buttons off the screen. 

`CTkPopup` automatically checks the height of your message before showing it:
- **Short Messages (under 300 pixels tall):** Displays inside a clean, centered text label.
- **Long Messages (over 300 pixels tall, like crash logs):** Automatically swaps the label for a clean, scrollable `CTkTextbox`.
  - Users can highlight any part of the text with their mouse.
  - Users can press **`Ctrl+C`** to copy the error traceback into their clipboard.
  - Buttons stay pinned neatly at the bottom.

---

## 9. Synchronous vs Asynchronous (Callbacks)

### 1. Synchronous Mode (Default)
Linear script execution pauses until the user closes the dialog. It returns the value directly:
```python
result = CTkPopup(master=app, text="Confirm operation?", buttons=["Yes", "No"]).get()
if result == "Yes":
    do_something()
```

### 2. Asynchronous Mode (`callback=...`)
If you do not want your code to freeze and wait, pass a `callback` function. Python moves straight to the next line immediately, and `CTkPopup` will trigger your function whenever the user clicks a button:

```python
def handle_response(choice):
    print("User finished dialog with choice:", choice)


# Execution continues immediately to the next line
CTkPopup(
    master=app,
    text="Exporting file in background...",
    buttons=["Stop", "Dismiss"],
    callback=handle_response,
)
print("This line prints immediately without waiting!")
```

---

## 10. CustomTkinter Dynamic Configuration (`.configure` & `.cget`)

As a true CustomTkinter citizen, `CTkPopup` rejects arbitrary property setters and getters. Every visual and functional property is read via `.cget()` and dynamically mutated via `.configure()`, exactly like standard `CTkButton` or `CTkLabel` widgets.

### 1. Reading Attributes with `.cget()`
```python
popup = CTkPopup(master=app, text="File uploaded.", title="Status", preset="info")

# Read current configuration safely
current_text = popup.cget("text")  # "File uploaded."
current_title = popup.cget("title")  # "Status"
current_preset = popup.cget("preset")  # "info"
```

### 2. Live Dynamic Mutation with `.configure()`
When a dialog is already on screen (for instance in non-blocking async mode), you can update its prompt, title, buttons, icon, or preset on the fly. The window geometry automatically resizes and re-centers seamlessly without screen flicker:

```python
popup = CTkPopup(
    master=app,
    text="Downloading file...",
    buttons=["Cancel"],
    preset="info",
)

# Later in your background process:
popup.configure(
    text="Download complete! Would you like to view it now?",
    title="Success",
    preset="success",
    buttons=[("Open File", True, "primary"), ("Close", False, "cancel")],
)
```

---

## 11. Icons & Smart Fallbacks

You can specify icons in three distinct ways:

### 1. Built-in Stock Icons
Pass any of the 5 built-in stock names as a clean keyword:

| Stock Icon Name | What It Shows |
| :--- | :--- |
| `"info"` | Blue circular informational "i" badge |
| `"warning"` | Amber caution triangle with exclamation mark |
| `"error"` | Red circular danger badge with "X" |
| `"question"` | Indigo circular question mark badge |
| `"success"` | Emerald green checkmark badge |

```python
# Use any stock icon directly by name
CTkPopup(master=app, text="File saved successfully.", icon="success").get()
```

### 2. Custom File Names & Paths
Whenever you want to use a specific file name, supply your own custom image asset:

```python
# Pass a path to your own custom PNG, ICO, or JPG file
CTkPopup(master=app, text="Custom Branding", icon="assets/my_logo.png").get()
```

> **Tip:** Relative paths (e.g. `icon="assets/my_logo.png"`) are automatically resolved whether running directly from source or packaged inside a PyInstaller frozen executable.

### 3. Pre-configured `ctk.CTkImage`
Pass a CustomTkinter image object directly when you need dedicated assets for Light and Dark modes:

```python
from PIL import Image

custom_icon = ctk.CTkImage(
    light_image=Image.open("assets/brand_dark.png"),
    dark_image=Image.open("assets/brand_light.png"),
    size=(64, 64),
)

CTkPopup(master=app, text="Theme-aware dialog", icon=custom_icon).get()
```

### The Smart Fall-Safe Rule
If you provide a custom icon path that does not exist or cannot be read, `CTkPopup` **never crashes your application**.
Instead:
- It prints a helpful developer warning to `sys.stderr`:  
  `[CTkPopup Warning]: Custom icon 'path' could not be resolved. Falling back to preset stock icon.`
- It automatically displays the preset's stock icon (such as the warning triangle), keeping your app stable and visually intact for end users.

---

## 12. Global Rebranding & Localization

If you are translating your application (e.g. to French or German), or if your company wants custom colors across every dialog in your entire app, you can configure presets once at the start of your program:

### 1. Translating Preset Defaults
```python
from ctkforge import CTkPopup

# Change the Question preset to French across your entire app
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

### 2. Changing Role Colors Globally
```python
# Change the destructive button color to custom orange-red
CTkPopup.ROLE_COLORS["destructive"] = {
    "fg_color": ("#E65100", "#FF6D00"),  # (Light Mode, Dark Mode)
    "hover_color": ("#BF360C", "#DD2C00"),  # (Light Mode, Dark Mode)
    "text_color": ("#FFFFFF", "#FFFFFF"),
}
```
