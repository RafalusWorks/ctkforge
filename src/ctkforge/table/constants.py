"""Global constants and layout thresholds for CTkTable."""

from typing import Final

# Event state modifier bitmasks in Tkinter
TK_SHIFT_MASK: Final[int] = 0x0001
TK_CONTROL_MASK: Final[int] = 0x0004

# Engine dimension & threshold defaults
MIN_COLUMN_WIDTH: Final[int] = 50
MIN_ROW_HEIGHT: Final[int] = 16
MIN_HEADER_HEIGHT: Final[int] = 20
DIVIDER_HOVER_TOLERANCE: Final[int] = 6
CELL_HORIZONTAL_PADDING: Final[int] = 8
DEFAULT_BORDER_SPACING: Final[int] = 5
DEFAULT_OVERSCAN_ROWS: Final[int] = 5
DEFAULT_OVERSCAN_COLS: Final[int] = 2
DEFAULT_ROW_HEIGHT: Final[int] = 28
DEFAULT_HEADER_HEIGHT: Final[int] = 32

# Mousewheel & scrolling step ratios
MOUSEWHEEL_STEP_ROWS: Final[int] = 3
MOUSEWHEEL_BASE_DELTA: Final[int] = 120
HORIZONTAL_SCROLL_STEP_PX: Final[int] = 80

# Auto-fit & text truncation thresholds
AUTOFIT_SAMPLE_ROWS: Final[int] = 200
AUTOFIT_PADDING_PX: Final[int] = 28
AUTOFIT_FALLBACK_WIDTH: Final[int] = 40
MIN_TEXT_MEASURE_WIDTH: Final[int] = 8
TEXT_ELLIPSIS: Final[str] = "..."

# Focus indicator ring style & editor frame
FOCUS_RING_DASH: Final[tuple[int, int]] = (2, 2)
EDITOR_BORDER_WIDTH: Final[int] = 2

# Canvas card arc angles
HEADER_ARC_START_LEFT: Final[int] = 90
HEADER_ARC_START_RIGHT: Final[int] = 0
HEADER_ARC_EXTENT: Final[int] = 90
