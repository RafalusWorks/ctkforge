"""CustomTkinter extension components and widgets.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from ctkforge.debug import (
    DEBUG_BANNER,
    enable_debug_mode,
    is_debug_mode,
    print_window_telemetry,
)
from ctkforge.geometry import scale, unscale
from ctkforge.popup import CTkPopup
from ctkforge.resources import resource_path
from ctkforge.spinbox import CTkSpinbox
from ctkforge.table import CTkTable

__version__ = "0.4.1"

__all__ = [
    "DEBUG_BANNER",
    "CTkPopup",
    "CTkSpinbox",
    "CTkTable",
    "__version__",
    "enable_debug_mode",
    "is_debug_mode",
    "print_window_telemetry",
    "resource_path",
    "scale",
    "unscale",
]
