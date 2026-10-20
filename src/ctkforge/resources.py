"""Resource and asset path resolver for Python apps packaged with PyInstaller.

Automatically resolves asset paths whether running from source or packaged
inside a PyInstaller executable—so your app doesn't crash on missing files.

Author: Rafalus
Repository: https://github.com/RafalusWorks/pyinstaller-resource-path
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

__author__: str = "Rafalus"
__all__: list[str] = ["resource_path"]


def resource_path(relative_path: str | Path, *, strict: bool = False) -> Path | None:
    """Resolve an absolute path to a resource for development and PyInstaller builds.

    Automatically resolves asset paths whether running from source or packaged
    inside a PyInstaller executable—so your app doesn't crash on missing files.

    Args:
        relative_path: Relative resource path as a string or Path object.
        strict: If False (default), returns None. If True, raises an exception.

    Returns:
        The resolved absolute Path if the target exists, or None when strict is False.

    Raises:
        ValueError: If relative_path is empty.
        FileNotFoundError: If the resource does not exist.

    Example:
        >>> icon_path = resource_path("assets/icon.png")
    """
    if not relative_path:
        if strict:
            raise ValueError("Resource path cannot be empty.")
        return None

    path_obj = Path(relative_path)
    checked: list[Path] = []

    if path_obj.is_absolute():
        warnings.warn(
            f"\nAbsolute path '{relative_path}' passed to resource_path(). "
            "Use relative paths to ensure cross-platform portability in frozen bundles.",
            UserWarning,
            stacklevel=2,
        )

    # 1. In frozen mode, PyInstaller bundle location takes highest priority
    #    to prevent accidental file leakage from the developer's local filesystem.
    if hasattr(sys, "_MEIPASS") and not path_obj.is_absolute():
        candidate = Path(sys._MEIPASS) / path_obj
        checked.append(candidate)
        if candidate.exists():
            return candidate.resolve()

    # 2. Direct path (relative to current working directory or absolute)
    checked.append(path_obj)
    if path_obj.exists():
        return path_obj.resolve()

    # 3. Development mode (relative to the entry script sys.argv[0])
    if sys.argv and sys.argv[0] and not path_obj.is_absolute():
        entry_dir = Path(sys.argv[0]).resolve().parent
        candidate = entry_dir / path_obj
        checked.append(candidate)
        if candidate.exists():
            return candidate.resolve()

    if strict:
        searched_paths = "\n  - ".join(str(p) for p in checked)
        raise FileNotFoundError(
            f"Resource '{relative_path}' could not be resolved.\n"
            f"Checked locations:\n  - {searched_paths}"
        )

    return None
