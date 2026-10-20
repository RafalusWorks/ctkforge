"""CTkPopup - A robust, modern, and DPI-aware dialog replacement for CTkMessagebox.

Features:
  - 4 semantic button roles (primary, cancel, destructive, normal) with dedicated resting and hover colors
  - Decoupled semantic return values (booleans, tokens)
  - Hidden-staging window lifecycle preventing geometry jumps
  - The Courier Rule: safe return values without widget destruction errors
  - Automatic switching to copyable CTkTextbox for long logs and exceptions
  - Option B Smart Fail-Safe icon resolution
"""

from .constants import PRESETS, ROLE_COLORS
from .popup import CTkPopup

__version__ = "1.0.0"
__all__ = [
    "PRESETS",
    "ROLE_COLORS",
    "CTkPopup",
]
