"""Icon resolution, loading, and high-DPI scaling for CTkPopup.

Internal helper module. Not part of the public API.
"""

import importlib.resources
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image

from ctkforge.resources import resource_path

from .constants import ICON_DISPLAY_SIZE, PRESETS

__all__: list[str] = []


def load_image_as_ctk(
    image_path: Path,
    display_size: tuple[int, int] = ICON_DISPLAY_SIZE,
) -> ctk.CTkImage:
    """Open an image file with Pillow and wrap it into a DPI-aware CTkImage.

    Pillow handles the master file (e.g., 256x256), while CustomTkinter downscales
    it using Lanczos filtering to the logical display size (e.g., 48x48).
    """
    with Image.open(image_path) as img:
        pil_img = img.copy()
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=display_size)


def load_stock_icon(
    icon_name: str,
    display_size: tuple[int, int] = ICON_DISPLAY_SIZE,
) -> ctk.CTkImage | None:
    """Load a bundled stock icon from the popup/icons/ package directory.

    Args:
        icon_name: Base name (e.g. 'warning' or 'warning.png').
        display_size: Target logical dimensions on screen.

    Returns:
        Configured ctk.CTkImage, or None if not found.
    """
    filename = icon_name if icon_name.endswith(".png") else f"{icon_name}.png"

    with suppress(OSError, TypeError, ValueError, ModuleNotFoundError):
        # Modern standard library package resource locator
        resource_ref = importlib.resources.files(__package__).joinpath("icons", filename)
        # In Python 3.9+, as_file yields a context or path
        with importlib.resources.as_file(resource_ref) as path:
            if path.is_file():
                return load_image_as_ctk(path, display_size)

    # Direct filesystem fallback for development / unpacked trees
    local_path = Path(__file__).resolve().parent / "icons" / filename
    if local_path.is_file():
        return load_image_as_ctk(local_path, display_size)

    return None


def resolve_icon(
    icon_input: Any,
    preset_name: str | None = None,
    display_size: tuple[int, int] = ICON_DISPLAY_SIZE,
) -> ctk.CTkImage | None:
    """Resolve an icon input through the fallback priority chain.

    Priority Chain:
      1. Pre-configured ctk.CTkImage -> use as-is.
      2. Preset keyword or bundled stock icon filename.
      3. Unified resource locator via resource_path (CWD, PyInstaller _MEIPASS, sys.argv[0]).
      4. Option B Smart Fail-Safe: Log warning and fall back to stock preset icon.

    Args:
        icon_input: Image object, file path, stock preset name, or None.
        preset_name: Optional active preset name (e.g., 'warning', 'error') for fallback.
        display_size: Target logical display size.

    Returns:
        ctk.CTkImage if resolved, or None if no icon can be shown.
    """
    if icon_input is None:
        if preset_name and preset_name in PRESETS:
            stock_name = PRESETS[preset_name].get("icon", f"{preset_name}.png")
            return load_stock_icon(stock_name, display_size)
        return None

    # Step 1: Already a ctk.CTkImage
    if isinstance(icon_input, ctk.CTkImage):
        return icon_input

    # If it's a known stock preset keyword (e.g. "warning", "info")
    if isinstance(icon_input, str) and icon_input in PRESETS:
        stock_name = PRESETS[icon_input].get("icon", f"{icon_input}.png")
        stock_img = load_stock_icon(stock_name, display_size)
        if stock_img is not None:
            return stock_img

    if isinstance(icon_input, (str, Path)):
        str_path = str(icon_input)

        # Also check if it's a stock icon filename directly (e.g., "warning.png")
        stock_img = load_stock_icon(str_path, display_size)
        if stock_img is not None:
            return stock_img

        # Step 2: Unified resource locator (CWD, PyInstaller _MEIPASS, sys.argv[0])
        resolved_file = resource_path(str_path)
        if resolved_file is not None and resolved_file.is_file():
            try:
                return load_image_as_ctk(resolved_file, display_size)
            except (OSError, ValueError) as e:
                print(
                    f"[CTkPopup Warning]: Error reading icon file '{resolved_file}': {e}",
                    file=sys.stderr,
                )

    # Step 5: Option B Smart Fail-Safe
    print(
        f"[CTkPopup Warning]: Custom icon '{icon_input}' could not be resolved. "
        f"Falling back to preset stock icon.",
        file=sys.stderr,
    )

    if preset_name and preset_name in PRESETS:
        stock_name = PRESETS[preset_name].get("icon", f"{preset_name}.png")
        return load_stock_icon(stock_name, display_size)

    return None
