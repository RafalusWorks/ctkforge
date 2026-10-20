"""Button normalization and styling helpers for CTkPopup.

Internal helper module. Not part of the public API.
"""

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from .constants import ROLE_COLORS

__all__: list[str] = []


def normalize_buttons(raw_buttons: Any) -> list[dict[str, Any]]:
    """Convert various button input styles into a standardized list of button dicts.

    Supported input formats:
      - Full dictionary:
          [{"text": "Delete", "value": "del", "role": "destructive"}]
      - Tuples:
          [("Save", True)]                     -> role defaults to "primary"
          [("Delete", False, "destructive")]  -> explicit role
      - Plain strings:
          ["OK"]               -> 1 button: role="primary"
          ["Yes", "No"]        -> 2 buttons: first="primary", second="cancel"
          ["Save", "Skip", "Cancel"] -> 3+ buttons: first="primary", last="cancel", middle="normal"

    Returns:
        List of dicts, each guaranteed to have 'text', 'value', and 'role' keys.
    """
    if not raw_buttons:
        return [{"text": "OK", "value": "ok", "role": "primary"}]

    # If developer accidentally passed a single string or dict instead of a list
    if isinstance(raw_buttons, (str, dict, tuple)):
        raw_buttons = [raw_buttons]

    normalized: list[dict[str, Any]] = []
    total = len(raw_buttons)

    for index, item in enumerate(raw_buttons):
        # 1. Full dictionary format
        if isinstance(item, dict):
            btn_text = str(item.get("text", item.get("label", "OK")))
            value = item.get("value", btn_text)
            role = str(item.get("role", "normal"))
            spec: dict[str, Any] = {"text": btn_text, "value": value, "role": role}

            # Standard CustomTkinter color overrides per button
            for color_key in ("fg_color", "hover_color", "text_color"):
                if color_key in item:
                    spec[color_key] = item[color_key]

            normalized.append(spec)

        # 2. Tuple format
        elif isinstance(item, tuple):
            if len(item) == 1:
                btn_text = str(item[0])
                value = btn_text
                role = "primary" if index == 0 else "normal"
            elif len(item) == 2:
                btn_text = str(item[0])
                value = item[1]
                role = "primary" if index == 0 else "normal"
            else:
                btn_text = str(item[0])
                value = item[1]
                role = str(item[2])
            normalized.append({"text": btn_text, "value": value, "role": role})

        # 3. Plain string format
        elif isinstance(item, str):
            btn_text = item
            value = item

            if total == 1:
                role = "primary"
            elif total == 2:
                role = "primary" if index == 0 else "cancel"
            else:
                if index == 0:
                    role = "primary"
                elif index == total - 1:
                    role = "cancel"
                else:
                    role = "normal"

            normalized.append({"text": btn_text, "value": value, "role": role})

        # Fallback for unrecognized types
        else:
            btn_text = str(item)
            normalized.append({"text": btn_text, "value": item, "role": "normal"})

    return normalized


def create_button(
    master: Any,
    spec: dict[str, Any],
    on_click: Callable[[Any], None],
    role_colors: dict[str, dict[str, Any]] | None = None,
) -> ctk.CTkButton:
    """Create a styled CTkButton based on its semantic role.

    Args:
        master: The parent container widget.
        spec: Button definition dictionary containing 'text', 'value', and 'role'.
        on_click: Callback function invoked with button's semantic value when clicked.
        role_colors: Optional role-to-color mapping overriding default ROLE_COLORS.

    Returns:
        Configured ctk.CTkButton instance.
    """
    colors_map = role_colors or ROLE_COLORS
    role = spec.get("role", "normal")
    styling = colors_map.get(role, colors_map.get("normal", {}))

    kwargs: dict[str, Any] = {
        "text": spec.get("text", spec.get("label", "OK")),
        "command": lambda: on_click(spec.get("value")),
        "height": 36,
        "corner_radius": 6,
    }

    # Only pass explicit colors if defined (None lets CTk inherit theme accent)
    if styling.get("fg_color") is not None:
        kwargs["fg_color"] = styling["fg_color"]
    if styling.get("hover_color") is not None:
        kwargs["hover_color"] = styling["hover_color"]
    if styling.get("text_color") is not None:
        kwargs["text_color"] = styling["text_color"]

    # Explicit per-button overrides take precedence
    for color_key in ("fg_color", "hover_color", "text_color"):
        if spec.get(color_key) is not None:
            kwargs[color_key] = spec[color_key]

    return ctk.CTkButton(master, **kwargs)
