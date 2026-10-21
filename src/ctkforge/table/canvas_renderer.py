"""Renders table headers, visible cell rows, selection highlights, and focus outlines onto Tkinter canvases.

This module provides the TableRenderer class, which paints column headers,
alternating row backgrounds, cell text, grid dividers, and focus rings. It also
trims overflowing text neatly with an ellipsis when columns are too narrow.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Any

import customtkinter as ctk

from ctkforge.table.constants import (
    FOCUS_RING_DASH,
    HEADER_ARC_EXTENT,
    HEADER_ARC_START_LEFT,
    HEADER_ARC_START_RIGHT,
    MIN_TEXT_MEASURE_WIDTH,
    TEXT_ELLIPSIS,
)
from ctkforge.table.data_model import TableDataModel
from ctkforge.table.selection_manager import SelectionManager


class TableRenderer:
    """Handles double-canvas rasterization for pinned headers, body viewport, and scrollbars."""

    @staticmethod
    def truncate_text(text: str, max_width: int, measure_font: tkfont.Font) -> str:
        """Clip and truncate text with an ellipsis if it exceeds the column width."""
        if max_width <= MIN_TEXT_MEASURE_WIDTH or not text:
            return ""
        if measure_font.measure(text) <= max_width:
            return text

        ellipsis_w = measure_font.measure(TEXT_ELLIPSIS)
        target_w = max_width - ellipsis_w
        if target_w <= 0:
            return TEXT_ELLIPSIS

        low = 0
        high = len(text)
        best = 0
        while low <= high:
            mid = (low + high) // 2
            if measure_font.measure(text[:mid]) <= target_w:
                best = mid
                low = mid + 1
            else:
                high = mid - 1

        return text[:best] + TEXT_ELLIPSIS

    def render_header(
        self,
        canvas: tk.Canvas,
        headers: list[str],
        col_widths: list[int],
        col_offsets: list[int],
        start_col: int,
        end_col: int,
        scroll_x: float,
        header_height: int,
        canvas_width: int,
        corner_radius: int,
        bg_hex: str,
        text_color_hex: str,
        divider_color_hex: str,
        header_font: Any,
        sort_col: int | None,
        sort_ascending: bool,
        scaled_padding: int,
    ) -> None:
        """Render the pinned table header bar with column dividers and sort glyphs."""
        canvas.delete("all")
        header_w = canvas.winfo_width()
        if header_w <= 1:
            header_w = canvas_width

        header_font_obj = tkfont.Font(font=header_font)
        radius = min(corner_radius, header_height, header_w // 2)

        if radius > 0 and header_w > 2 * radius:
            canvas.create_arc(
                0, 0, 2 * radius, 2 * radius,
                start=HEADER_ARC_START_LEFT, extent=HEADER_ARC_EXTENT, fill=bg_hex, outline="",
            )
            canvas.create_arc(
                header_w - 2 * radius, 0, header_w, 2 * radius,
                start=HEADER_ARC_START_RIGHT, extent=HEADER_ARC_EXTENT, fill=bg_hex, outline="",
            )
            canvas.create_rectangle(radius, 0, header_w - radius, header_height, fill=bg_hex, outline="")
            canvas.create_rectangle(0, radius, header_w, header_height, fill=bg_hex, outline="")
        else:
            canvas.create_rectangle(0, 0, header_w, header_height, fill=bg_hex, outline="")

        # Bottom border line
        canvas.create_line(0, header_height - 1, header_w, header_height - 1, fill=divider_color_hex)

        # Columns
        for c in range(start_col, end_col):
            x_left = col_offsets[c] - scroll_x
            col_w = col_widths[c]
            max_w = col_w - (scaled_padding * 2)

            if c > 0:
                canvas.create_line(x_left, 0, x_left, header_height, fill=divider_color_hex)

            base_title = headers[c] if c < len(headers) else f"Col {c + 1}"
            if sort_col == c:
                sort_arrow = " ▲" if sort_ascending else " ▼"
                header_title = base_title + sort_arrow
            else:
                header_title = base_title

            disp_title = self.truncate_text(header_title, max_w, header_font_obj)
            canvas.create_text(
                x_left + scaled_padding,
                header_height // 2,
                text=disp_title,
                anchor="w",
                fill=text_color_hex,
                font=header_font,
            )

    def render_body(
        self,
        canvas: tk.Canvas,
        data_model: TableDataModel,
        selection_manager: SelectionManager,
        col_widths: list[int],
        col_offsets: list[int],
        start_col: int,
        end_col: int,
        start_row: int,
        end_row: int,
        scroll_x: float,
        scroll_y: float,
        scaled_row_height: int,
        canvas_width: int,
        text_color_hex: str,
        selected_bg_hex: str,
        selected_text_hex: str,
        row_even_bg: str,
        row_odd_bg: str,
        divider_color_hex: str,
        body_font: Any,
        scaled_padding: int,
    ) -> None:
        """Render rows and cells within the visible viewport."""
        canvas.delete("all")
        if data_model.row_count == 0 or len(col_widths) == 0:
            return

        body_font_obj = tkfont.Font(font=body_font)
        is_row_target = selection_manager.target == "row"

        for r in range(start_row, end_row):
            y_top = r * scaled_row_height - scroll_y
            y_bottom = y_top + scaled_row_height
            is_row_selected = is_row_target and r in selection_manager.selected_rows

            row_bg = selected_bg_hex if is_row_selected else (row_even_bg if r % 2 == 0 else row_odd_bg)

            # Row background
            canvas.create_rectangle(0, y_top, canvas_width, y_bottom, fill=row_bg, outline="")
            # Horizontal divider line
            canvas.create_line(0, y_bottom, canvas_width, y_bottom, fill=divider_color_hex)

            raw_row = data_model.get_raw_row_index(r)
            row_data = data_model.values[raw_row]
            row_len = len(row_data)

            for c in range(start_col, min(end_col, row_len)):
                x_left = col_offsets[c] - scroll_x
                x_right = col_offsets[c + 1] - scroll_x
                col_w = col_widths[c]
                max_text_w = col_w - (scaled_padding * 2)

                is_cell_selected = not is_row_target and (r, c) in selection_manager.selected_cells

                if is_cell_selected:
                    canvas.create_rectangle(x_left, y_top, x_right, y_bottom, fill=selected_bg_hex, outline="")

                if c > 0:
                    canvas.create_line(x_left, y_top, x_left, y_bottom, fill=divider_color_hex)

                current_text_color = selected_text_hex if (is_row_selected or is_cell_selected) else text_color_hex
                display_val = self.truncate_text(str(row_data[c]), max_text_w, body_font_obj)

                canvas.create_text(
                    x_left + scaled_padding,
                    y_top + (scaled_row_height // 2),
                    text=display_val,
                    anchor="w",
                    fill=current_text_color,
                    font=body_font,
                )

            # Focus indicator ring
            if is_row_target and selection_manager.focused_row == r:
                canvas.create_rectangle(
                    1, y_top + 1, canvas_width - 2, y_bottom - 1,
                    outline=divider_color_hex, dash=FOCUS_RING_DASH,
                )

    @staticmethod
    def sync_scrollbars(
        v_scrollbar: ctk.CTkScrollbar,
        h_scrollbar: ctk.CTkScrollbar,
        scroll_x: float,
        scroll_y: float,
        total_content_width: int,
        total_content_height: int,
        canvas_width: int,
        canvas_height: int,
    ) -> None:
        """Update vertical and horizontal scrollbar slider positions."""
        if total_content_height <= canvas_height or total_content_height <= 0:
            v_scrollbar.set(0.0, 1.0)
        else:
            v_first = scroll_y / total_content_height
            v_last = min(1.0, (scroll_y + canvas_height) / total_content_height)
            v_scrollbar.set(v_first, v_last)

        if total_content_width <= canvas_width or total_content_width <= 0:
            h_scrollbar.set(0.0, 1.0)
        else:
            h_first = scroll_x / total_content_width
            h_last = min(1.0, (scroll_x + canvas_width) / total_content_width)
            h_scrollbar.set(h_first, h_last)
