"""Comprehensive automated test suite for CTkTable."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from ctkforge.table import CTkTable

DEMO_HEADERS: list[str] = ["ID", "Name", "Department", "Salary (£)", "Status"]
DEMO_SORT_KEY: dict[int | str, str] = {0: "int", 3: "int"}
DEMO_DATA: list[list[Any]] = [
    [101, "Alice Morgan", "Engineering", 125000, "Active"],
    [102, "Bob Vance", "Sales", 82000, "Active"],
    [103, "Charlie Day", "Logistics", 45000, "On Leave"],
    [104, "Dana Scully", "Research", 110000, "Active"],
    [105, "Edward Nygma", "Security", 95000, "Active"],
    [106, "Fiona Gallagher", "Operations", 67000, "Inactive"],
    [107, "George Costanza", "Management", 55000, "Probation"],
    [108, "Harriet Tubman", "Legal", 140000, "Active"],
]


def run_table_test_suite(table: CTkTable, root: ctk.CTk) -> None:
    """Execute all 24 automated tests on a table instance."""

    def step() -> None:
        root.update()

    def clean_slate_reset() -> None:
        """Reset table data, selection, sorting, configuration, and column widths to clean baseline."""
        table._cancel_edit()
        table.clear_selection()
        table.clear_sort()
        table.configure(
            values=[list(r) for r in DEMO_DATA],
            selection_target="row",
            selection_mode="extended",
            row_height=28,
            column_widths=None,
        )
        table.scroll_to(row=0, col=0)
        root.update()

    # Clean-slate reset before test run begins
    clean_slate_reset()

    # 1. Initial State & Dimensions
    step()
    assert table.get_cell(0, 1) == "Alice Morgan", "Initial row 0 cell 1 mismatch"
    assert table.get_sort_state() == (None, True), "Initial sort state should be None"
    print("[1/25] Initial State & Dimensions: PASSED", flush=True)

    # 2. Sort by Salary Ascending (column 3)
    table.sort_by(3, ascending=True)
    step()
    assert table.get_cell(0, 1) == "Charlie Day", "Lowest salary Charlie Day should be row 0"
    assert table.get_cell(7, 1) == "Harriet Tubman", "Highest salary Harriet should be row 7"
    assert table.get_sort_state() == (3, True), "Sort state should be (3, True)"
    print("[2/25] Sort by Salary Ascending: PASSED", flush=True)

    # 3. Sort by Salary Descending (column 3)
    table.sort_by(3, ascending=False)
    step()
    assert table.get_cell(0, 1) == "Harriet Tubman", "Highest salary Harriet should be row 0"
    assert table.get_sort_state() == (3, False), "Sort state should be (3, False)"
    print("[3/25] Sort by Salary Descending: PASSED", flush=True)

    # 4. Clear Sort (Restore initial insertion order)
    table.clear_sort()
    step()
    assert table.get_cell(0, 1) == "Alice Morgan", "Alice should return to row 0"
    assert table.get_sort_state() == (None, True), "Sort state should be cleared"
    print("[4/25] Clear Sort (Restore insertion order): PASSED", flush=True)

    # 5. Row Selection
    table.clear_selection()
    table.select_row(1)
    step()
    assert table.get_selected_rows() == [1], "Row 1 should be selected"
    table.clear_selection()
    step()
    assert table.get_selected_rows() == [], "Selection should be empty"
    print("[5/25] Row Selection: PASSED", flush=True)

    # 6. Range Selection (Rows 1 to 3)
    table._selection_manager.apply_click(1, 0)
    table._selection_manager.apply_click(3, 0, is_shift=True)
    table._redraw()
    step()
    assert set(table.get_selected_rows()) == {1, 2, 3}, "Rows 1-3 should be selected"
    table.clear_selection()
    step()
    print("[6/25] Range Selection: PASSED", flush=True)

    # 7. Select All and Deselect
    table.select_all()
    step()
    assert len(table.get_selected_rows()) == 8, "All 8 rows should be selected"
    table.clear_selection()
    step()
    assert table.get_selected_rows() == [], "Selection should be empty after clear"
    print("[7/25] Select All and Deselect: PASSED", flush=True)

    # 8. In-Place Cell Editing and Commit
    table._start_editing(2, 2)
    assert table.is_editing and table._editor._entry is not None, "Editor failed to spawn on cell (2, 2)"
    step()
    table._editor._entry.delete(0, "end")
    table._editor._entry.insert(0, "Operations")
    step()
    table._commit_edit()
    assert table.get_cell(2, 2) == "Operations", "Cell (2, 2) should update to 'Operations'"
    table.update_cell(2, 2, "Logistics")
    step()
    print("[8/25] In-Place Cell Editing and Commit: PASSED", flush=True)

    # 9. In-Place Cell Editing Cancellation (Escape)
    table._start_editing(0, 1)
    assert table.is_editing and table._editor._entry is not None, "Editor failed to spawn on cell (0, 1)"
    step()
    table._editor._entry.delete(0, "end")
    table._editor._entry.insert(0, "Temporary Draft")
    step()
    table._cancel_edit()
    assert table.get_cell(0, 1) == "Alice Morgan", "Cell (0, 1) should remain unchanged"
    step()
    print("[9/25] In-Place Cell Editing Cancellation: PASSED", flush=True)

    # 10. Locked / Non-Editable Column and Baseline Preservation
    # Baseline is True, column 0 locked:
    table.configure(editable={"default": True, 0: False})
    table._start_editing(0, 0)
    assert not table.is_editing, "Editing column 0 should be blocked"
    table._start_editing(0, 1)
    assert table.is_editing, "Editing column 1 should be allowed"
    table._cancel_edit()

    # Later reconfigure without 'default': baseline (True) must survive
    table.configure(editable={1: False})
    table._start_editing(0, 1)
    assert not table.is_editing, "Editing column 1 should now be blocked"
    table._start_editing(0, 2)
    assert table.is_editing, "Editing column 2 should still be allowed under preserved True default"
    table._cancel_edit()

    table.configure(editable=True)

    # Header sortable dict and baseline preservation:
    # Baseline is True, column 0 not sortable:
    table.configure(header_sortable={0: False})
    assert not table._is_column_header_sortable(0), "Column 0 should not be sortable"
    assert table._is_column_header_sortable(1), "Column 1 should be sortable under True default"

    # Reconfigure without 'default': baseline (True) must survive
    table.configure(header_sortable={2: False})
    assert not table._is_column_header_sortable(2), "Column 2 should not be sortable"
    assert table._is_column_header_sortable(1), "Column 1 should still be sortable"

    table.configure(header_sortable=True)
    step()
    print("[10/25] Locked / Non-Editable Column and Header Sortable Rules: PASSED", flush=True)

    # 11. Selection Modes (Cell vs Row)
    table.configure(selection_target="cell")
    table.select_cell(0, 1)
    step()
    assert table.get_selected_cells() == [(0, 1)], "Cell (0, 1) should be selected"
    table.clear_selection()
    table.configure(selection_target="row")
    step()
    print("[11/25] Selection Modes (Cell vs Row): PASSED", flush=True)

    # 12. Dirty Numeric Sorting
    table.configure(
        values=[
            [1, "Item A", "Dept", "$50", "Active"],
            [2, "Item B", "Dept", "12-34-56", "Active"],
            [3, "Item C", "Dept", "10", "Active"],
        ]
    )
    table.sort_by(3, ascending=True)
    step()
    assert table.get_sort_state() == (3, True), "Dirty numeric sort should succeed"
    table.configure(values=[list(r) for r in DEMO_DATA])
    table.clear_sort()
    step()
    print("[12/25] Dirty Numeric Sorting: PASSED", flush=True)

    # 13. Insert Row with Active Sort
    table.sort_by(3, ascending=True)
    table.insert_row(values=[109, "Zack Morris", "Support", 30000, "Active"])
    step()
    assert table.get_cell(0, 1) == "Zack Morris", "Lowest salary Zack should sort to row 0"
    print("[13/25] Insert Row with Active Sort: PASSED", flush=True)

    # 14. Delete Row
    table.delete_rows(0)
    step()
    assert table.get_cell(0, 1) == "Charlie Day", "Charlie Day should return to row 0"
    table.clear_sort()
    step()
    print("[14/25] Delete Row: PASSED", flush=True)

    # 15. Auto-Fit Column & Dynamic Style Configuration
    table.auto_fit_column(1)
    step()
    assert table._column_widths is not None, "Column widths should be computed"
    table.configure(column_widths=None)
    step()
    table.configure(row_height=34)
    step()
    assert table.cget("row_height") == 34, "Row height should update to 34"
    table.configure(row_height=28)
    step()
    print("[15/25] Auto-Fit Column & Style Configuration: PASSED", flush=True)

    # 16. Scrolling and Viewport Clamping
    table.configure(values=[[100 + i, f"Employee {i}", "Dept", 50000 + i * 1000, "Active"] for i in range(40)])
    root.update()
    table.scroll_to(row=35)
    step()
    assert table._scroll_y > 0.0, "Viewport should scroll down to row 35"
    table.scroll_to(row=0)
    step()
    assert table._scroll_y == 0.0, "Viewport should scroll back to top"
    print("[16/25] Scrolling and Viewport Clamping: PASSED", flush=True)

    # 17. Index Resolution (Display <-> Raw)
    clean_slate_reset()
    table.sort_by(3, ascending=True)
    step()
    assert table.get_raw_row_index(0) == 2, "Lowest salary should map to raw index 2"
    assert table.get_display_row_index(2) == 0, "Raw index 2 should map to display row 0"
    assert table.get_raw_row_index([0, 1]) == [2, 6], "List of display indexes should translate to list"
    assert table.get_display_row_index([2, 6]) == [0, 1], "List of raw indexes should translate to list"
    table.clear_sort()
    step()
    assert table.get_raw_row_index(2) == 2, "Unsorted display row 2 maps to raw index 2"
    assert table.get_display_row_index(2) == 2, "Unsorted raw index 2 maps to display row 2"
    assert table.get_raw_row_index([1, 2]) == [1, 2], "Unsorted list should translate 1:1"
    print("[17/25] Index Resolution (Display <-> Raw): PASSED", flush=True)

    # 18. Atomic Row Update
    table.update_row(0, [999, "Alice Updated", "Engineering", 130000, "Active"], notify=False)
    step()
    row_0 = table.get_row(0)
    assert row_0[0] == 999 and row_0[1] == "Alice Updated", "Row 0 should update atomically"
    table.sort_by(3, ascending=True)
    step()
    disp_lowest = 0
    raw_target = table.get_raw_row_index(disp_lowest)
    table.update_row(disp_lowest, [103, "Charlie Day", "Logistics", 200000, "Promoted"], notify=False)
    step()
    assert table.get_raw_row_index(0) != raw_target, "Re-sort should move promoted record"
    print("[18/25] Atomic Row Update: PASSED", flush=True)

    # 19. Batched Auto-Fit Columns
    table.auto_fit_columns()
    step()
    assert isinstance(table._column_widths, (list, dict)), "Column widths should be populated"
    print("[19/25] Batched Auto-Fit Columns: PASSED", flush=True)

    # 20. Justify, Header Alignments, and Sort Key (Dict with default key)
    table.configure(
        justify={"default": "left", 0: "center", 3: "right"},
        header_alignment="center",
        sort_key={"default": "str", 0: "int", 3: "int"},
    )
    step()
    assert table.cget("justify") == {"default": "left", 0: "center", 3: "right"}
    assert table.cget("header_alignment") == "center"
    assert table.cget("sort_key") == {"default": "str", 0: "int", 3: "int"}

    # Custom callable sort key (sort by Name length)
    table.configure(sort_key={1: lambda s: len(str(s))})
    table.sort_by(1, ascending=True)
    step()
    assert len(table.get_cell(0, 1)) <= len(table.get_cell(7, 1))
    table.configure(sort_key={"default": "str", 0: "int", 3: "int"})
    table.clear_sort()

    col_norm = table._get_normalized_column_alignments()
    assert col_norm[0] == "center"
    assert col_norm[1] == "left"
    assert col_norm[3] == "right"
    h_norm = table._get_normalized_header_alignments()
    assert h_norm[0] == "center"
    assert h_norm[3] == "center"
    print("[20/25] Justify and Header Alignments: PASSED", flush=True)

    # 21. Unified Text Colors (with 'default' key and override)
    table.configure(
        text_color={"default": "#ffffff", 1: "#ff0000", 3: ("#112233", "#aabbcc")},
        header_text_color={"default": "#3b8ed0", 0: "#00ff00"},
    )
    step()
    assert table.cget("text_color") == {"default": "#ffffff", 1: "#ff0000", 3: ("#112233", "#aabbcc")}
    assert table.cget("header_text_color") == {"default": "#3b8ed0", 0: "#00ff00"}
    assert table._cached_colors["text"] == "#ffffff"
    assert table._cached_colors["header_text"] == "#3b8ed0"
    assert table._cached_col_text_colors[1] == "#ff0000"
    assert table._cached_header_text_colors[0] == "#00ff00"
    print("[21/25] Column and Header Text Colors: PASSED", flush=True)

    # 22. Unified Fonts with Shortcuts and 'default' key
    table.configure(
        font={1: "bold", 2: "italic", 3: "bold italic"},
        header_font={0: "bold"},
    )
    step()
    assert 1 in table._cached_col_fonts
    assert 1 in table._cached_col_font_objs
    assert 0 in table._cached_header_fonts
    assert 0 in table._cached_header_font_objs
    print("[22/25] Column and Header Fonts with Shortcuts: PASSED", flush=True)

    # 23. Header Hover State & Interactive Pointer Dispatching
    table.configure(
        header_hover_color="#335577",
        header_sortable={"default": True, 3: False},
    )
    step()
    assert table.cget("header_hover_color") == "#335577"

    class MockEvent:
        def __init__(self, x: int, y: int = 10) -> None:
            self.x = x
            self.y = y

    cw = table._table_canvas.winfo_width()
    _, offsets = table._calculate_column_geometry(cw)

    # Sortable column 1 hover sets hover highlight and hand cursor
    col1_mid_x = (offsets[1] + offsets[2]) // 2
    table._on_header_motion(MockEvent(col1_mid_x))
    assert table._hovered_header_col == 1
    assert table._current_header_cursor == "hand2"

    # Button release over header preserves hover and hand cursor
    table._on_header_release(MockEvent(col1_mid_x))
    assert table._hovered_header_col == 1
    assert table._current_header_cursor == "hand2"

    # Rapid sequential clicks on header body toggle sorting through Double-Button-1 delegation
    table.clear_sort()
    table._on_header_click(MockEvent(col1_mid_x))
    table._on_header_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (1, True)

    # Rapid second click arriving as Double-Button-1 toggles sort to descending
    table._on_header_double_click(MockEvent(col1_mid_x))
    table._on_header_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (1, False)

    # Rapid third click arriving as Triple-Button-1 clears sort
    table._on_header_double_click(MockEvent(col1_mid_x))
    table._on_header_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (None, True)

    # Unsortable column 3 hover does not highlight and keeps default arrow cursor
    col3_mid_x = (offsets[3] + offsets[4]) // 2
    table._on_header_motion(MockEvent(col3_mid_x))
    assert table._hovered_header_col is None
    assert table._current_header_cursor == ""

    # Mouse leave resets hover highlight and restores cursor
    table._on_header_leave(MockEvent(0))
    assert table._hovered_header_col is None
    assert table._current_header_cursor == ""
    print("[23/25] Header Hover & Interactive Pointer Dispatching: PASSED", flush=True)

    # 24. Divider Double-Click Auto-Fit & Resizing Drag Immunity
    div1_x = offsets[1]
    table._on_header_motion(MockEvent(div1_x))
    assert table._current_header_cursor == "sb_h_double_arrow"

    # Pressing down divider arms drag resizing
    table._on_header_click(MockEvent(div1_x))
    assert table._column_resizer.is_resizing

    # Double click auto-fits and immediately disarms drag resizing
    table._on_header_double_click(MockEvent(div1_x))
    assert not table._column_resizer.is_resizing
    w_autofit = table._column_widths[0]

    # Subsequent motion jitter while lifting mouse button must be ignored
    table._on_header_drag(MockEvent(div1_x + 5))
    assert table._column_widths[0] == w_autofit
    table._on_header_release(MockEvent(div1_x + 5))

    # Coordinate fallback when divider hover was momentarily cleared
    table._column_resizer.clear_hover()
    table._on_header_double_click(MockEvent(div1_x + 3))
    assert table._column_widths[0] == w_autofit
    print("[24/25] Divider Double-Click Auto-Fit & Drag Immunity: PASSED", flush=True)

    # 25. In-Place Editor Custom Font & Justify Pass-Through
    table._start_editing(0, 3)
    step()
    assert table._editor.is_editing
    assert table._editor._entry is not None
    assert table._editor._entry.cget("justify") == "right"
    table._cancel_edit()
    step()
    assert not table._editor.is_editing
    print("[25/25] Cell Editor Styling Integration: PASSED", flush=True)

    # Baseline State Restoration (Identical Clean-Slate Reset)
    clean_slate_reset()


def run_headless_tests() -> None:
    """Run comprehensive automated assertions in headless mode."""
    print("Running automated sanity tests (headless)...")
    root = ctk.CTk()
    root.geometry("800x600+9999+9999")
    root.deiconify()
    root.update()

    table = CTkTable(
        root,
        headers=DEMO_HEADERS,
        values=[list(r) for r in DEMO_DATA],
        editable=True,
        sort_key=DEMO_SORT_KEY,
        selection_mode="extended",
        selection_target="row",
    )
    table.pack(fill="both", expand=True)
    root.update()

    run_table_test_suite(table, root)
    root.destroy()
    print("All automated checks (25/25) passed successfully!")


def test_ctktable() -> None:
    """Entry point for automated pytest test runner discovery."""
    run_headless_tests()


def test_theme_color_pair_not_unpacked_as_columns() -> None:
    """Verify that 2-element theme color lists are not unpacked as per-column colors."""
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.geometry("400x300+9999+9999")
    table = CTkTable(root, headers=["ID", "Name"], values=[[1, "Alice"]])
    table.pack()
    root.update()

    assert table._cached_col_text_colors == {}
    assert table._cached_header_text_colors == {}

    header_fills = [
        table._header_canvas.itemcget(item, "fill")
        for item in table._header_canvas.find_all()
        if table._header_canvas.type(item) == "text"
    ]
    assert header_fills == ["#DCE4EE", "#DCE4EE"]

    body_fills = [
        table._table_canvas.itemcget(item, "fill")
        for item in table._table_canvas.find_all()
        if table._table_canvas.type(item) == "text"
    ]
    assert body_fills == ["#DCE4EE", "#DCE4EE"]
    root.destroy()


def test_column_color_dict_styling() -> None:
    """Verify dictionary-based column color overrides with default declared first."""
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.geometry("400x300+9999+9999")
    table = CTkTable(
        root,
        headers=["ID", "Status"],
        values=[[101, "Active"]],
        text_color={"default": ("gray10", "#DCE4EE"), 1: "#2ecc71"},
        header_text_color={"default": ("gray10", "#DCE4EE"), 1: "#3a7ebf"},
    )
    table.pack()
    root.update()

    header_text_items = [
        (table._header_canvas.itemcget(i, "text"), table._header_canvas.itemcget(i, "fill"))
        for i in table._header_canvas.find_all()
        if table._header_canvas.type(i) == "text"
    ]
    assert ("ID", "#DCE4EE") in header_text_items
    assert ("Status", "#3a7ebf") in header_text_items

    body_text_items = [
        (table._table_canvas.itemcget(i, "text"), table._table_canvas.itemcget(i, "fill"))
        for i in table._table_canvas.find_all()
        if table._table_canvas.type(i) == "text"
    ]
    assert ("101", "#DCE4EE") in body_text_items
    assert ("Active", "#2ecc71") in body_text_items

    ctk.set_appearance_mode("Light")
    root.update()

    light_body_items = [
        (table._table_canvas.itemcget(i, "text"), table._table_canvas.itemcget(i, "fill"))
        for i in table._table_canvas.find_all()
        if table._table_canvas.type(i) == "text"
    ]
    assert ("101", "gray10") in light_body_items
    assert ("Active", "#2ecc71") in light_body_items

    root.destroy()
    ctk.set_appearance_mode("Dark")


if __name__ == "__main__":
    run_headless_tests()
