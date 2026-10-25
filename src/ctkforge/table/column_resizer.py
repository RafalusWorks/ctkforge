"""Detects column divider hover, manages mouse drag resizing, and calculates auto-fit widths.

Tracks divider boundaries, calculates new column widths during mouse drag operations,
and measures text to find the best column width automatically.
"""

from collections.abc import Callable


class ColumnResizer:
    """Manages the interactive dragging, hover detection, and auto-fitting of table columns."""

    def __init__(self) -> None:
        """Initialize divider drag tracking and hover state."""
        self._hover_divider_col: int | None = None
        self._resizing_col: int | None = None
        self._resize_start_x: int = 0
        self._resize_start_w: int = 0

    @property
    def hover_divider_col(self) -> int | None:
        """Return the divider index currently under the mouse cursor, or None."""
        return self._hover_divider_col

    @property
    def is_resizing(self) -> bool:
        """Return True if a column drag-resize operation is actively in progress."""
        return self._resizing_col is not None

    @property
    def resizing_col(self) -> int | None:
        """Return the column index currently being resized, or None."""
        return self._resizing_col

    def check_divider_hover(
        self,
        logical_x: float,
        col_offsets: list[int],
        tolerance: float,
    ) -> int | None:
        """Find which column divider line is within tolerance of the given X coordinate.

        Returns:
            The matched divider index (1 to N), or None if no divider is close enough.
        """
        matched_divider: int | None = None
        for c in range(1, len(col_offsets)):
            if abs(logical_x - col_offsets[c]) <= tolerance:
                matched_divider = c
                break

        self._hover_divider_col = matched_divider
        return matched_divider

    def clear_hover(self) -> None:
        """Clear active divider hover state."""
        self._hover_divider_col = None

    def start_resize(self, col: int, mouse_x: int, current_col_width: int) -> int:
        """Initialize a drag-resize operation for a column.

        Args:
            col: The logical index of the column to resize.
            mouse_x: The starting mouse X coordinate.
            current_col_width: The current width of the column being resized.

        Returns:
            The index of the column being resized.
        """
        self._resizing_col = col
        self._resize_start_x = mouse_x
        self._resize_start_w = current_col_width
        return self._resizing_col

    def calculate_drag_width(self, mouse_x: int, min_width: int) -> int:
        """Calculate the new column width based on mouse movement during drag.

        Args:
            mouse_x: Current mouse X coordinate.
            min_width: Minimum allowable column width constraint.

        Returns:
            The clamped new column width in pixels.
        """
        if self._resizing_col is None:
            return min_width

        delta_x = mouse_x - self._resize_start_x
        return max(min_width, self._resize_start_w + delta_x)

    def end_resize(self) -> None:
        """Complete and reset the column drag-resize operation."""
        self._resizing_col = None

    @staticmethod
    def calculate_autofit_width(
        header_text: str | None,
        sample_values: list[str],
        header_measure: Callable[[str], int],
        body_measure: Callable[[str], int],
        padding: int,
        fallback_width: int,
    ) -> int:
        """Calculate the ideal column width to fit header text and sample cell values.

        Args:
            header_text: Optional title text of the column.
            sample_values: String representations of sample cell values.
            header_measure: Function measuring pixel width with the header font.
            body_measure: Function measuring pixel width with the body font.
            padding: Total horizontal padding to add around cell text.
            fallback_width: Default base width if text is shorter.

        Returns:
            The calculated pixel width needed to show the content comfortably.
        """
        max_text_w = fallback_width
        if header_text:
            max_text_w = max(max_text_w, header_measure(header_text))

        for val in sample_values:
            if val:
                max_text_w = max(max_text_w, body_measure(val))

        return max_text_w + padding
