"""Configuration constants, presets, and role color palettes for CTkPopup.

All presets and role colors are defined at the module/class level so developers
can customize themes and localization in one central place.
"""

from typing import Any

# fmt: off
# Layout dimensions and thresholds
MAX_LABEL_HEIGHT: int = 300
TEXTBOX_HEIGHT: int = 220
TEXTBOX_WIDTH_PADDING: int = 40
DEFAULT_POPUP_WIDTH: int = 478  # Baseline width (floor is ~355px for 2 buttons; ~478px fits full wrap 340 + icon 138)
DEFAULT_WRAPLENGTH: int = 340  # Maximum horizontal wrap boundary for text
ICON_DISPLAY_SIZE: tuple[int, int] = (64, 64)

# Styling and typography tokens
MESSAGE_FONT_SIZE: int = 13
POPUP_BORDER_COLOR: tuple[str, str] = ("gray80", "gray25")
POPUP_BORDER_WIDTH: int = 1
# fmt: on

# Color definitions for the 4 essential button roles.
# Each role contains light and dark mode hex tuples: (light_color, dark_color).
# "primary" uses None so it automatically inherits CustomTkinter's active accent color.
ROLE_COLORS: dict[str, dict[str, Any]] = {
    "primary": {
        "fg_color": None,
        "hover_color": None,
        "text_color": None,
    },
    "destructive": {
        "fg_color": ("#DC2626", "#EF4444"),
        "hover_color": ("#B91C1C", "#DC2626"),
        "text_color": ("#FFFFFF", "#FFFFFF"),
    },
    "cancel": {
        "fg_color": ("#E5E7EB", "#374151"),
        "hover_color": ("#D1D5DB", "#4B5563"),
        "text_color": ("#1F2937", "#F9FAFB"),
    },
    "normal": {
        "fg_color": ("#F3F4F6", "#1F2937"),
        "hover_color": ("#E5E7EB", "#374151"),
        "text_color": ("#374151", "#E5E7EB"),
    },
}

# The 5 standard preset configurations for dialogs.
# Exposes only title, icon, buttons, and keyboard action defaults.
# Button layout follows Windows Standard (Microsoft Guidelines):
# Primary action comes first (left), and Cancel is on the far right:
#   [ Proceed ]  [ Cancel ]
#   [ Delete ]   [ Cancel ]
#   [ Yes ]      [ No ]
# (Windows users read left-to-right and expect the affirmative action first).
PRESETS: dict[str, dict[str, Any]] = {
    "info": {
        "title": "Information",
        "icon": "info.png",
        "buttons": [{"label": "OK", "value": "ok", "role": "primary"}],
        "default_button": "ok",
        "cancel_button": "ok",
    },
    "warning": {
        "title": "Warning",
        "icon": "warning.png",
        "buttons": [
            {"label": "Proceed", "value": True, "role": "primary"},
            {"label": "Cancel", "value": False, "role": "cancel"},
        ],
        "default_button": True,
        "cancel_button": False,
    },
    "error": {
        "title": "Error",
        "icon": "error.png",
        "buttons": [{"label": "Dismiss", "value": "dismiss", "role": "destructive"}],
        "default_button": "dismiss",
        "cancel_button": "dismiss",
    },
    "question": {
        "title": "Confirm",
        "icon": "question.png",
        "buttons": [
            {"label": "Yes", "value": True, "role": "primary"},
            {"label": "No", "value": False, "role": "cancel"},
        ],
        "default_button": True,
        "cancel_button": False,
    },
    "success": {
        "title": "Success",
        "icon": "success.png",
        "buttons": [{"label": "OK", "value": "ok", "role": "primary"}],
        "default_button": "ok",
        "cancel_button": "ok",
    },
}

# Public customization tables (safe for application-wide customization).
# All other constants in this file are internal layout defaults subject to change.
__all__ = [
    "PRESETS",
    "ROLE_COLORS",
]
