"""Renders table headers, visible cell rows, selection highlights, and focus outlines onto Tkinter canvases.

Paints column headers, alternating row backgrounds, cell text, grid dividers,
and focus rings. Trims overflowing text neatly with an ellipsis when columns
are too narrow.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
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
        headers: list[str] | None,
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
        header_alignments: dict[int, str] | None = None,
        header_text_colors: dict[int, str] | None = None,
        header_fonts: dict[int, Any] | None = None,
        header_font_objs: dict[int, tkfont.Font] | None = None,
        hovered_col: int | None = None,
        header_hover_color_hex: str | None = None,
        visible_cols: list[int] | None = None,
    ) -> None:
        """Render the pinned table header bar with column dividers and sort glyphs."""
        canvas.delete("all")
        if len(col_widths) == 0:
            return
        header_w = canvas.winfo_width()
        if header_w <= 1:
            header_w = canvas_width

        total_content_right = col_offsets[-1] - scroll_x if col_offsets else 0
        content_right = max(0, min(header_w, int(total_content_right)))
        if content_right <= 0:
            return

        header_font_obj = tkfont.Font(font=header_font)
        radius = min(corner_radius, header_height, content_right // 2)

        has_left_arc = radius > 0 and scroll_x == 0
        has_right_arc = radius > 0

        if has_left_arc or has_right_arc:
            left_offset = radius if has_left_arc else 0
            right_offset = radius if has_right_arc else 0

            if has_left_arc:
                canvas.create_arc(
                    0,
                    0,
                    2 * radius,
                    2 * radius,
                    start=HEADER_ARC_START_LEFT,
                    extent=HEADER_ARC_EXTENT,
                    fill=bg_hex,
                    outline="",
                )
            if has_right_arc:
                canvas.create_arc(
                    content_right - 2 * radius,
                    0,
                    content_right,
                    2 * radius,
                    start=HEADER_ARC_START_RIGHT,
                    extent=HEADER_ARC_EXTENT,
                    fill=bg_hex,
                    outline="",
                )
            if content_right > left_offset + right_offset:
                canvas.create_rectangle(
                    left_offset, 0, content_right - right_offset, header_height, fill=bg_hex, outline=""
                )
            canvas.create_rectangle(0, radius, content_right, header_height, fill=bg_hex, outline="")
        else:
            canvas.create_rectangle(0, 0, content_right, header_height, fill=bg_hex, outline="")

        # Draw hover background behind the active column if hovered
        total_cols = len(col_widths)
        if hovered_col is not None and header_hover_color_hex and 0 <= hovered_col < total_cols:
            h_left = col_offsets[hovered_col] - scroll_x
            h_right = col_offsets[hovered_col + 1] - scroll_x
            is_first = hovered_col == 0 and has_left_arc
            is_last = hovered_col == total_cols - 1 and has_right_arc

            if is_first or is_last:
                h_left_offset = radius if is_first else 0
                h_right_offset = radius if is_last else 0
                if is_first:
                    canvas.create_arc(
                        h_left,
                        0,
                        h_left + 2 * radius,
                        2 * radius,
                        start=HEADER_ARC_START_LEFT,
                        extent=HEADER_ARC_EXTENT,
                        fill=header_hover_color_hex,
                        outline="",
                    )
                if is_last:
                    canvas.create_arc(
                        h_right - 2 * radius,
                        0,
                        h_right,
                        2 * radius,
                        start=HEADER_ARC_START_RIGHT,
                        extent=HEADER_ARC_EXTENT,
                        fill=header_hover_color_hex,
                        outline="",
                    )
                if h_right > h_left + h_left_offset + h_right_offset:
                    canvas.create_rectangle(
                        h_left + h_left_offset,
                        0,
                        h_right - h_right_offset,
                        header_height,
                        fill=header_hover_color_hex,
                        outline="",
                    )
                canvas.create_rectangle(h_left, radius, h_right, header_height, fill=header_hover_color_hex, outline="")
            else:
                canvas.create_rectangle(h_left, 0, h_right, header_height, fill=header_hover_color_hex, outline="")

        # Bottom border line
        canvas.create_line(0, header_height - 1, content_right, header_height - 1, fill=divider_color_hex)

        # Columns
        for v_col in range(start_col, end_col):
            x_left = col_offsets[v_col] - scroll_x
            x_right = col_offsets[v_col + 1] - scroll_x
            col_w = col_widths[v_col]
            max_w = col_w - (scaled_padding * 2)

            if v_col > 0:
                canvas.create_line(x_left, 0, x_left, header_height, fill=divider_color_hex)

            c = visible_cols[v_col] if visible_cols is not None else v_col

            # Determine column-specific header font and color
            col_h_font = header_fonts[c] if (header_fonts and c in header_fonts) else header_font
            col_h_font_obj = header_font_objs[c] if (header_font_objs and c in header_font_objs) else header_font_obj
            col_h_color = header_text_colors[c] if (header_text_colors and c in header_text_colors) else text_color_hex

            base_title = headers[c] if (headers is not None and c < len(headers)) else ""
            if sort_col == c:
                glyph = "▲" if sort_ascending else "▼"
                header_title = f"{base_title} {glyph}" if base_title else glyph
            else:
                header_title = base_title

            disp_title = self.truncate_text(header_title, max_w, col_h_font_obj)

            # Determine text placement and anchor based on header alignment
            h_align = header_alignments.get(c, "left") if header_alignments else "left"
            if h_align == "center":
                anchor = "center"
                x_pos = (x_left + x_right) / 2
            elif h_align == "right":
                anchor = "e"
                x_pos = x_right - scaled_padding
            else:
                anchor = "w"
                x_pos = x_left + scaled_padding

            canvas.create_text(
                x_pos,
                header_height // 2,
                text=disp_title,
                anchor=anchor,
                fill=col_h_color,
                font=col_h_font,
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
        column_alignments: dict[int, str] | None = None,
        col_text_colors: dict[int, str] | None = None,
        col_fonts: dict[int, Any] | None = None,
        col_font_objs: dict[int, tkfont.Font] | None = None,
        visible_cols: list[int] | None = None,
        resolve_color: Callable[[Any], str] | None = None,
    ) -> None:
        """Render rows and cells within the visible viewport."""
        canvas.delete("all")
        if data_model.row_count == 0 or len(col_widths) == 0:
            return

        body_font_obj = tkfont.Font(font=body_font)
        is_row_target = selection_manager.target == "row"
        num_visible = len(col_widths)

        for r in range(start_row, end_row):
            y_top = r * scaled_row_height - scroll_y
            y_bottom = y_top + scaled_row_height
            is_row_selected = is_row_target and r in selection_manager.selected_rows

            row_bg = selected_bg_hex if is_row_selected else (row_even_bg if r % 2 == 0 else row_odd_bg)

            # Row background
            canvas.create_rectangle(0, y_top, canvas_width, y_bottom, fill=row_bg, outline="")
            # Horizontal divider line
            canvas.create_line(0, y_bottom, canvas_width, y_bottom, fill=divider_color_hex)

            storage_row = data_model.get_storage_index(r)
            row_data = data_model.values[storage_row]
            row_len = len(row_data)
            row_id = data_model.get_row_id(r)
            cell_colors = data_model.get_cell_text_colors_for_row_id(row_id)

            for v_col in range(start_col, min(end_col, num_visible)):
                c = visible_cols[v_col] if visible_cols is not None else v_col
                if c >= row_len:
                    continue

                x_left = col_offsets[v_col] - scroll_x
                x_right = col_offsets[v_col + 1] - scroll_x
                col_w = col_widths[v_col]
                max_text_w = col_w - (scaled_padding * 2)

                is_cell_selected = not is_row_target and (r, c) in selection_manager.selected_cells

                if is_cell_selected:
                    canvas.create_rectangle(x_left, y_top, x_right, y_bottom, fill=selected_bg_hex, outline="")

                if v_col > 0:
                    canvas.create_line(x_left, y_top, x_left, y_bottom, fill=divider_color_hex)
                if v_col == num_visible - 1:
                    canvas.create_line(x_right, y_top, x_right, y_bottom, fill=divider_color_hex)

                # Prioritize selection color over custom cell and column text color
                if is_row_selected or is_cell_selected:
                    current_text_color = selected_text_hex
                elif cell_colors and c in cell_colors:
                    current_text_color = (
                        resolve_color(cell_colors[c]) if resolve_color is not None else str(cell_colors[c])
                    )
                elif col_text_colors and c in col_text_colors:
                    current_text_color = col_text_colors[c]
                else:
                    current_text_color = text_color_hex

                # Resolve column font and font measurement object
                cell_font = col_fonts[c] if (col_fonts and c in col_fonts) else body_font
                cell_font_obj = col_font_objs[c] if (col_font_objs and c in col_font_objs) else body_font_obj

                display_val = self.truncate_text(str(row_data[c]), max_text_w, cell_font_obj)

                # Position text according to column alignment
                align = column_alignments.get(c, "left") if column_alignments else "left"
                if align == "center":
                    anchor = "center"
                    x_pos = (x_left + x_right) / 2
                elif align == "right":
                    anchor = "e"
                    x_pos = x_right - scaled_padding
                else:
                    anchor = "w"
                    x_pos = x_left + scaled_padding

                canvas.create_text(
                    x_pos,
                    y_top + (scaled_row_height // 2),
                    text=display_val,
                    anchor=anchor,
                    fill=current_text_color,
                    font=cell_font,
                )

            # Focus indicator ring
            if is_row_target and selection_manager.focused_row == r:
                canvas.create_rectangle(
                    1,
                    y_top + 1,
                    canvas_width - 2,
                    y_bottom - 1,
                    outline=divider_color_hex,
                    dash=FOCUS_RING_DASH,
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
