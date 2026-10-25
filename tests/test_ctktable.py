"""Comprehensive automated test suite for CTkTable."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from ctkforge.geometry import scale
from ctkforge.table import CTkTable
from ctkforge.table.constants import MIN_COLUMN_WIDTH

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
    assert not table._header_controller.is_column_sortable(0), "Column 0 should not be sortable"
    assert table._header_controller.is_column_sortable(1), "Column 1 should be sortable under True default"

    # Reconfigure without 'default': baseline (True) must survive
    table.configure(header_sortable={2: False})
    assert not table._header_controller.is_column_sortable(2), "Column 2 should not be sortable"
    assert table._header_controller.is_column_sortable(1), "Column 1 should still be sortable"

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
    assert table.get_displayed_header(1) == table.get_header(1), "Unsorted header should match base title"
    table.sort_by(1, ascending=True)
    assert "▲" in table.get_displayed_header(1), "Sorted header should display up arrow"
    table.sort_by(1, ascending=False)
    assert "▼" in table.get_displayed_header(1), "Descending header should display down arrow"
    table.clear_sort()

    table.auto_fit_column(1)
    step()
    assert table._layout_mgr.column_widths is not None, "Column widths should be computed"
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
    assert table._scroll_controller.scroll_y > 0.0, "Viewport should scroll down to row 35"
    table.scroll_to(row=0)
    step()
    assert table._scroll_controller.scroll_y == 0.0, "Viewport should scroll back to top"
    print("[16/25] Scrolling and Viewport Clamping: PASSED", flush=True)

    # 17. Row ID & Display Resolution and Freeze Sort
    clean_slate_reset()
    table.sort_by(3, ascending=True)
    step()
    assert table.get_row_id(0) == 2, "Lowest salary should map to row_id 2"
    assert table.get_display_row(2) == 0, "Row ID 2 should map to display row 0"
    assert table.get_row_id([0, 1]) == [2, 6], "List of display indexes should translate to row_ids"
    assert table.get_display_row([2, 6]) == [0, 1], "List of row_ids should translate to display indexes"
    assert table.get_row_by_id(2)[1] == "Charlie Day", "get_row_by_id should return row data"

    # Test freeze_sort
    table.freeze_sort()
    step()
    assert table.get_sort_state() == (None, True), "freeze_sort should clear active sort state"
    assert table.get_row_id(0) == 2, "Lowest salary should STILL map to row_id 2 after freeze_sort"
    assert table.get_display_row(2) == 0, "Row ID 2 should STILL map to display row 0 after freeze_sort"

    # Verify inserted row receives unique row_id
    new_disp = table.insert_row(values=[777, "New Employee", "Tech", 80000, "Active"])
    new_id = table.get_row_id(new_disp)
    assert new_id >= 8, "New row should receive a unique auto-incremented row_id"
    assert table.get_row_by_id(new_id)[1] == "New Employee", "get_row_by_id should retrieve inserted row"
    table.delete_rows(new_disp)
    print("[17/25] Row ID & Display Resolution: PASSED", flush=True)

    # 18. Atomic Row Update
    table.update_row(0, [999, "Alice Updated", "Engineering", 130000, "Active"], notify=False)
    step()
    row_0 = table.get_row(0)
    assert row_0[0] == 999 and row_0[1] == "Alice Updated", "Row 0 should update atomically"
    table.sort_by(3, ascending=True)
    step()
    disp_lowest = 0
    id_target = table.get_row_id(disp_lowest)
    table.update_row(disp_lowest, [103, "Charlie Day", "Logistics", 200000, "Promoted"], notify=False)
    step()
    assert table.get_row_id(0) != id_target, "Re-sort should move promoted record"
    print("[18/25] Atomic Row Update: PASSED", flush=True)

    # 19. Batched Auto-Fit Columns
    table.auto_fit_columns()
    step()
    assert isinstance(table._layout_mgr.column_widths, dict), "Column widths should be populated as a dict"
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

    col_norm = table._style.get_column_alignments()
    assert col_norm[0] == "center"
    assert col_norm[1] == "left"
    assert col_norm[3] == "right"
    h_norm = table._style.get_header_alignments()
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
    assert table._style.colors["text"] == "#ffffff"
    assert table._style.colors["header_text"] == "#3b8ed0"
    assert table._style.column_text_colors[1] == "#ff0000"
    assert table._style.header_text_colors[0] == "#00ff00"
    print("[21/25] Column and Header Text Colors: PASSED", flush=True)

    # 22. Unified Fonts with Shortcuts and 'default' key
    table.configure(
        font={1: "bold", 2: "italic", 3: "bold italic"},
        header_font={0: "bold"},
    )
    step()
    assert 1 in table._style.column_fonts
    assert 1 in table._style.column_font_objs
    assert 0 in table._style.header_fonts
    assert 0 in table._style.header_font_objs
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
    _, offsets = table._layout_mgr.calculate_geometry(cw)

    # Sortable column 1 hover sets hover highlight and hand cursor
    col1_mid_x = (offsets[1] + offsets[2]) // 2
    table._header_controller.on_motion(MockEvent(col1_mid_x))
    assert table._header_controller.hovered_col == 1
    assert table._header_controller.current_cursor == "hand2"

    # Button release over header preserves hover and hand cursor
    table._header_controller.on_release(MockEvent(col1_mid_x))
    assert table._header_controller.hovered_col == 1
    assert table._header_controller.current_cursor == "hand2"

    # Rapid sequential clicks on header body toggle sorting through Double-Button-1 delegation
    table.clear_sort()
    table._header_controller.on_click(MockEvent(col1_mid_x))
    table._header_controller.on_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (1, True)

    # Rapid second click arriving as Double-Button-1 toggles sort to descending
    table._header_controller.on_double_click(MockEvent(col1_mid_x))
    table._header_controller.on_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (1, False)

    # Rapid third click arriving as Triple-Button-1 clears sort
    table._header_controller.on_double_click(MockEvent(col1_mid_x))
    table._header_controller.on_release(MockEvent(col1_mid_x))
    assert table.get_sort_state() == (None, True)

    # Unsortable column 3 hover does not highlight and keeps default arrow cursor
    col3_mid_x = (offsets[3] + offsets[4]) // 2
    table._header_controller.on_motion(MockEvent(col3_mid_x))
    assert table._header_controller.hovered_col is None
    assert table._header_controller.current_cursor == ""

    # Mouse leave resets hover highlight and restores cursor
    table._header_controller.on_leave(MockEvent(0))
    assert table._header_controller.hovered_col is None
    assert table._header_controller.current_cursor == ""
    print("[23/25] Header Hover & Interactive Pointer Dispatching: PASSED", flush=True)

    # 24. Divider Double-Click Auto-Fit & Resizing Drag Immunity
    div1_x = offsets[1]
    table._header_controller.on_motion(MockEvent(div1_x))
    assert table._header_controller.current_cursor == "sb_h_double_arrow"

    # Pressing down divider arms drag resizing
    table._header_controller.on_click(MockEvent(div1_x))
    assert table._header_controller.column_resizer.is_resizing

    # Double click auto-fits and immediately disarms drag resizing
    table._header_controller.on_double_click(MockEvent(div1_x))
    assert not table._header_controller.column_resizer.is_resizing
    w_autofit = table._layout_mgr.column_widths[0]

    # Subsequent motion jitter while lifting mouse button must be ignored
    table._header_controller.on_drag(MockEvent(div1_x + 5))
    assert table._layout_mgr.column_widths[0] == w_autofit
    table._header_controller.on_release(MockEvent(div1_x + 5))

    # Coordinate fallback when divider hover was momentarily cleared
    table._header_controller.column_resizer.clear_hover()
    table._header_controller.on_double_click(MockEvent(div1_x + 3))
    assert table._layout_mgr.column_widths[0] == w_autofit
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

    assert table._style.column_text_colors == {}
    assert table._style.header_text_colors == {}

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


def test_column_widths_flex_and_auto() -> None:
    """Verify column_widths flex and auto layout calculation and clamping."""
    root = ctk.CTk()
    root.geometry("600x400+9999+9999")
    table = CTkTable(
        root,
        headers=["Col 0", "Col 1", "Col 2"],
        values=[[1, 2, 3]],
    )
    table.pack(fill="both", expand=True)
    root.update()

    min_w = scale(table, MIN_COLUMN_WIDTH)

    # 1. Uniform int width: all columns fixed to 120px scaled
    table.configure(column_widths=120)
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    assert col_w == [scale(table, 120), scale(table, 120), scale(table, 120)]

    # 2. Uniform auto: all columns evenly split available canvas width (600 / 3 = 200)
    table.configure(column_widths="auto")
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    assert col_w == [200, 200, 200]

    # 3. None also defaults to uniform auto
    table.configure(column_widths=None)
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    assert col_w == [200, 200, 200]

    # 4. Dict with "default": "auto", fixed col 0 (100) and fixed col 2 (150).
    # Col 1 is auto, taking the remaining slack: 600 - scale(100) - scale(150)
    table.configure(column_widths={"default": "auto", 0: 100, 2: 150})
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    expected_w0 = scale(table, 100)
    expected_w2 = scale(table, 150)
    expected_w1 = 600 - expected_w0 - expected_w2
    assert col_w == [expected_w0, expected_w1, expected_w2]

    # 5. Dict where "default" is omitted: defaults to "auto"
    table.configure(column_widths={0: 100, 2: 150})
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    assert col_w == [expected_w0, expected_w1, expected_w2]

    # 6. Multiple auto columns distribute slack equally
    # Col 0 is fixed (100). Remaining slack is 600 - expected_w0.
    # Col 1 and Col 2 split slack evenly.
    table.configure(column_widths={"default": "auto", 0: 100})
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    slack = 600 - expected_w0
    assert col_w[0] == expected_w0
    assert col_w[1] + col_w[2] == slack
    assert abs(col_w[1] - col_w[2]) <= 1

    # 7. Fixed width below MIN_COLUMN_WIDTH (40px) clamps to min_col_w
    table.configure(column_widths={"default": "auto", 0: 15, 1: 180, 2: 170})
    col_w, _ = table._layout_mgr.calculate_geometry(600)
    assert col_w[0] == min_w
    assert col_w[1] == scale(table, 180)
    assert col_w[2] == scale(table, 170)

    # 8. Viewport narrower than fixed widths clamps auto columns to min_col_w
    table.configure(column_widths={"default": "auto", 0: 200, 2: 200})
    col_w, _ = table._layout_mgr.calculate_geometry(300)
    assert col_w[0] == scale(table, 200)
    assert col_w[1] == min_w
    assert col_w[2] == scale(table, 200)

    # 9. Resizing any column when "auto" is active freezes all columns (Behavior A: no squishing)
    table.configure(column_widths={"default": "auto"})
    root.update()
    canvas_w = table._layout_mgr._get_canvas_width()
    col_w_before, _ = table._layout_mgr.calculate_geometry(canvas_w)
    table._layout_mgr.set_column_width(0, scale(table, 400))
    col_w_after, _ = table._layout_mgr.calculate_geometry(canvas_w)
    assert col_w_after[0] == scale(table, 400)
    assert col_w_after[1] == col_w_before[1]
    assert col_w_after[2] == col_w_before[2]

    # 10. Expanding window retains fixed widths for all columns, including the last column
    col_w_expanded, _ = table._layout_mgr.calculate_geometry(canvas_w + 500)
    assert col_w_expanded[0] == scale(table, 400)
    assert col_w_expanded[1] == col_w_before[1]
    assert col_w_expanded[2] == col_w_before[2]

    root.destroy()


def test_show_headers_visibility() -> None:
    """Verify show_headers controls header grid visibility, preserves names, and enables blank headers."""

    class Event:
        def __init__(self, x: int = 0, y: int = 10) -> None:
            self.x = x
            self.y = y

    root = ctk.CTk()
    root.geometry("600x400+9999+9999")

    # 1. Default with headers: show_headers is True and canvas is mapped
    table1 = CTkTable(root, headers=["A", "B"], values=[[1, 2]])
    table1.pack(fill="both", expand=True)
    root.update()
    assert table1.cget("show_headers") is True
    assert table1._header_canvas.winfo_ismapped()

    # 2. Hide headers: show_headers is False, headers preserved, canvas un-gridded
    table1.configure(show_headers=False)
    root.update()
    assert table1.cget("show_headers") is False
    assert table1.cget("headers") == ["A", "B"]
    assert not table1._header_canvas.winfo_ismapped()

    # 3. Restore headers: show_headers is True, canvas re-gridded
    table1.configure(show_headers=True)
    root.update()
    assert table1.cget("show_headers") is True
    assert table1._header_canvas.winfo_ismapped()
    table1.destroy()

    # 4. Default without headers: show_headers is False and canvas un-gridded
    table2 = CTkTable(root, values=[[10, 20]])
    table2.pack(fill="both", expand=True)
    root.update()
    assert table2.cget("show_headers") is False
    assert not table2._header_canvas.winfo_ismapped()
    table2.destroy()

    # 5. Explicit show_headers=True with headers=None: blank clickable headers for sorting
    table3 = CTkTable(root, values=[[20, 2], [10, 1]], show_headers=True)
    table3.pack(fill="both", expand=True)
    root.update()
    assert table3.cget("show_headers") is True
    assert table3.cget("headers") is None
    assert table3._get_total_cols() == 2
    assert table3._header_canvas.winfo_ismapped()

    # Click col 0 header to sort ascending
    table3._header_controller.on_click(Event(x=20))
    root.update()
    assert table3.get_sort_state() == (0, True)
    assert table3.get_cell(0, 0) == 10

    # Click col 0 header again to sort descending
    table3._header_controller.on_click(Event(x=20))
    root.update()
    assert table3.get_sort_state() == (0, False)
    assert table3.get_cell(0, 0) == 20

    table3.destroy()
    root.destroy()


def test_dictionary_and_partial_headers() -> None:
    """Verify dictionary-based header creation, partial patching, get_header, and set_header."""
    root = ctk.CTk()
    root.geometry("600x400+9999+9999")

    # 1. Initialize with list
    table = CTkTable(root, headers=["ID", "Name", "Role"], values=[[1, "Alice", "Admin"]])
    table.pack()
    root.update()
    assert table.cget("headers") == ["ID", "Name", "Role"]
    assert table.get_header(1) == "Name"

    # 2. Update specific header via set_header
    table.set_header(1, "Full Name")
    root.update()
    assert table.cget("headers") == ["ID", "Full Name", "Role"]
    assert table.get_header(1) == "Full Name"
    assert table.get_header(0) == "ID"
    assert table.get_header(2) == "Role"

    # 3. Patch via configure dict
    table.configure(headers={2: "Job Title"})
    root.update()
    assert table.cget("headers") == ["ID", "Full Name", "Job Title"]

    # 4. Sparse dict initialization
    table2 = CTkTable(root, headers={0: "Code", 2: "Cost"}, values=[[101, "Widget", 19.99]])
    table2.pack()
    root.update()
    assert table2.cget("headers") == ["Code", "", "Cost"]
    assert table2.get_header(0) == "Code"
    assert table2.get_header(1) == ""
    assert table2.get_header(2) == "Cost"

    # 5. Dict with "default" key
    table3 = CTkTable(root, headers={"default": "Data", 0: "ID"}, values=[[1, 2, 3]])
    table3.pack()
    root.update()
    assert table3.cget("headers") == ["ID", "Data", "Data"]

    table.destroy()
    table2.destroy()
    table3.destroy()
    root.destroy()


def test_copy_selection_asymmetric_column_and_row_lengths() -> None:
    """Verify clipboard export with both surplus and missing row values."""
    root = ctk.CTk()
    root.geometry("500x350+9999+9999")

    # Table with 3 headers:
    # Row 0 has 5 values (2 surplus hidden values: "Hidden1", "Hidden2")
    # Row 1 has 2 values (1 missing value for column 2)
    table = CTkTable(
        root,
        headers=["Col 0", "Col 1", "Col 2"],
        values=[
            [101, "Alice", "Active", "Hidden1", "Hidden2"],
            [102, "Bob"],
        ],
        copyable=True,
        selection_mode="extended",
    )
    table.pack()
    root.update()

    # --- Scenario A: Surplus values (5 values in 3 columns) ---
    # 1. Row mode exports all 5 values
    table.select_row(0)
    assert table.copy_selection() == "101\tAlice\tActive\tHidden1\tHidden2"

    # 2. Cell mode exports only visible selected cells (3 values)
    table.configure(selection_target="cell")
    table.clear_selection(notify=False)
    table.select_cell(0, 0)
    table.select_cell(0, 1)
    table.select_cell(0, 2)
    assert table.copy_selection() == "101\tAlice\tActive"

    # --- Scenario B: Missing values (2 values in 3 columns) ---
    # 3. Row mode exports only the 2 existing values
    table.configure(selection_target="row")
    table.clear_selection(notify=False)
    table.select_row(1)
    assert table.copy_selection() == "102\tBob"

    # 4. Cell mode exports 3 slots, with missing column 2 as empty string
    table.configure(selection_target="cell")
    table.clear_selection(notify=False)
    table.select_cell(1, 0)
    table.select_cell(1, 1)
    table.select_cell(1, 2)
    assert table.copy_selection() == "102\tBob\t"

    table.destroy()
    root.destroy()


def test_show_columns_visibility_and_interaction() -> None:
    """Verify show_columns boolean and dictionary overrides, geometry, hit-testing, and dynamic toggling."""
    root = ctk.CTk()
    root.geometry("800x500+9999+9999")

    table = CTkTable(
        root,
        headers=["ID", "Name", "Department", "Salary", "Status"],
        values=[
            [101, "Alice", "Engineering", 120000, "Active"],
            [102, "Bob", "Sales", 80000, "Active"],
            [103, "Charlie", "Logistics", 45000, "On Leave"],
        ],
        show_columns={"default": True, "Department": False, 3: False},
    )
    table.pack(fill="both", expand=True)
    root.update()

    # 1. Active visible columns should only be [0, 1, 4] ("ID", "Name", "Status")
    assert table._layout_mgr.get_visible_columns() == [0, 1, 4]
    cw = table._table_canvas.winfo_width()
    col_w, col_offsets = table._layout_mgr.calculate_geometry(cw)
    assert len(col_w) == 3
    assert len(col_offsets) == 4

    # 2. Hit testing: clicking visible column index 2 maps to logical column 4 ("Status")
    x_pos = (col_offsets[2] + col_offsets[3]) // 2
    cell = table._get_cell_at(x_pos, 10)
    assert cell == (0, 4)

    # 3. Dynamic toggle via configure: hide Name (1) and show Salary (3)
    table.configure(show_columns={"Name": False, "Salary": True})
    root.update()
    assert table._layout_mgr.get_visible_columns() == [0, 3, 4]

    # 4. Hide all columns: show_columns=False
    table.configure(show_columns=False)
    root.update()
    assert table._layout_mgr.get_visible_columns() == []
    cw, co = table._layout_mgr.calculate_geometry(600)
    assert cw == []
    assert co == [0]

    # 5. Restore all columns: show_columns=True
    table.configure(show_columns=True)
    root.update()
    assert table._layout_mgr.get_visible_columns() == [0, 1, 2, 3, 4]

    table.destroy()
    root.destroy()


def test_named_header_keys_scoped_attributes() -> None:
    """Verify that all column-scoped attributes accept header title strings as dictionary keys."""
    root = ctk.CTk()
    root.geometry("800x500+9999+9999")

    table = CTkTable(
        root,
        headers=["ID", "Name", "Department", "Salary", "Status"],
        values=[
            [101, "Alice", "Engineering", 120000, "Active"],
            [102, "Bob", "Sales", 80000, "Active"],
        ],
        column_widths={"default": "auto", "ID": 70, "Salary": 140},
        editable={"default": False, "Name": True},
        header_sortable={"default": True, "Status": False},
        justify={"default": "left", "ID": "center", "Salary": "right"},
        text_color={"Salary": "#2ecc71"},
        font={"Name": "bold"},
        sort_key={"ID": "int", "Salary": "int"},
        header_alignment={"ID": "center", "Salary": "right"},
        header_text_color={"ID": "#ff0000"},
        header_font={"Status": "bold"},
        show_columns={"Department": False},
    )
    table.pack(fill="both", expand=True)
    root.update()

    # Verify column_widths resolved "ID" -> 0 (70) and "Salary" -> 3 (140)
    default_w, norm_w = table._style.normalize_scoped_dict(table.cget("column_widths"))
    assert default_w == "auto"
    assert norm_w[0] == 70
    assert norm_w[3] == 140

    # Verify editable resolved "Name" -> 1
    assert table._is_column_editable(0) is False
    assert table._is_column_editable(1) is True
    assert table._is_column_editable(3) is False

    # Verify header_sortable resolved "Status" -> 4
    assert table._header_controller.is_column_sortable(0) is True
    assert table._header_controller.is_column_sortable(4) is False

    # Verify justify resolved "ID" -> 0, "Salary" -> 3
    alignments = table._style.get_column_alignments()
    assert alignments[0] == "center"
    assert alignments[3] == "right"
    assert alignments[1] == "left"

    # Verify text_color resolved "Salary" -> 3
    text_colors = table._style.get_column_text_colors()
    assert text_colors[3] == "#2ecc71"

    # Verify sort_key resolved "ID" -> 0, "Salary" -> 3
    assert table._data_model._sort_key_cols[0] == "int"
    assert table._data_model._sort_key_cols[3] == "int"

    # Verify header_alignment resolved "ID" -> 0, "Salary" -> 3
    h_align = table._style.get_header_alignments()
    assert h_align[0] == "center"
    assert h_align[3] == "right"

    # Verify show_columns resolved "Department" -> 2
    assert table._layout_mgr.is_column_shown(2) is False
    assert table._layout_mgr.is_column_shown(0) is True
    assert table._layout_mgr.get_visible_columns() == [0, 1, 3, 4]

    table.destroy()
    root.destroy()


def test_keyboard_navigation_and_shortcuts() -> None:
    """Verify arrow, paging, Home/End, Space, Escape, and Ctrl+A keys move focus and change selection."""
    root = ctk.CTk()
    root.geometry("800x500+9999+9999")

    table = CTkTable(
        root,
        headers=["ID", "Name", "Department", "Salary"],
        values=[[i, f"Name {i}", "Dept", i * 1000] for i in range(100)],
        selection_mode="extended",
        show_columns={"Department": False},
        selection_target="cell",
    )
    table.pack(fill="both", expand=True)
    root.update()
    table._table_canvas.focus_force()
    root.update()

    def press(key: str) -> None:
        table._table_canvas.event_generate(key)
        root.update()

    selection = table._selection_manager

    # With no prior focus, navigation starts from the first visible cell and moves one step per press
    press("<Down>")
    assert (selection.focused_row, selection.focused_col) == (1, 0)
    press("<Down>")
    press("<Right>")
    assert (selection.focused_row, selection.focused_col) == (2, 1)

    # Moving right from Name skips the hidden Department column and lands on Salary
    press("<Right>")
    assert selection.focused_col == 3

    # Moving past the last column or the first row stays put
    press("<Right>")
    assert selection.focused_col == 3
    press("<Home>")
    assert selection.focused_row == 0
    press("<Up>")
    assert selection.focused_row == 0

    # End jumps to the last row, and Page Up moves back by a screenful
    press("<End>")
    assert selection.focused_row == 99
    page_rows = table._scroll_controller.get_page_row_count()
    press("<Prior>")
    assert selection.focused_row == 99 - page_rows
    press("<Next>")
    assert selection.focused_row == 99

    # Navigation selects the focused cell, so Space toggles it off and then back on
    assert selection.selected_cells == {(99, 3)}
    press("<space>")
    assert not selection.selected_cells
    press("<space>")
    assert selection.selected_cells == {(99, 3)}

    # Escape clears the selection
    press("<Escape>")
    assert not selection.selected_cells

    # Ctrl+A selects everything
    press("<Control-a>")
    assert len(selection.selected_cells) == 100 * 4

    table.destroy()
    root.destroy()


def test_divider_drag_resizes_column_left_of_divider() -> None:
    """Verify dragging a divider widens only the column on its left, even when columns are hidden."""
    root = ctk.CTk()
    root.geometry("900x500+9999+9999")

    table = CTkTable(
        root,
        headers=["ID", "Name", "Department", "Salary", "Status"],
        values=[[1, "Alice", "Engineering", 120000, "Active"]],
        show_columns={"Name": False},
    )
    table.pack(fill="both", expand=True)
    root.update()

    class MockEvent:
        def __init__(self, x: int) -> None:
            self.x = x
            self.y = 10

    header = table._header_controller
    visible_cols = table._layout_mgr.get_visible_columns()
    assert visible_cols == [0, 2, 3, 4]

    for divider in range(1, len(visible_cols) + 1):
        table.configure(column_widths={"default": 120})
        root.update()
        _, offsets = table._layout_mgr.calculate_geometry(table._table_canvas.winfo_width())
        divider_x = offsets[divider]

        header.on_motion(MockEvent(divider_x))
        header.on_click(MockEvent(divider_x))
        assert header.column_resizer.resizing_col == visible_cols[divider - 1]

        header.on_drag(MockEvent(divider_x + 60))
        header.on_release(MockEvent(divider_x + 60))

        widths = table.cget("column_widths")
        resized = {col for col in widths if col != "default"}
        assert resized == {visible_cols[divider - 1]}
        assert widths[visible_cols[divider - 1]] > 120

    table.destroy()
    root.destroy()


def test_scroll_wheel_scrollbars_and_clamping() -> None:
    """Verify mouse wheel, scrollbar commands, edge clamping, and scroll_to move the view correctly."""
    root = ctk.CTk()
    root.geometry("600x400+9999+9999")

    table = CTkTable(
        root,
        headers=["A", "B", "C", "D", "E", "F"],
        values=[[f"{r}-{c}" for c in range(6)] for r in range(200)],
        column_widths=300,
    )
    table.pack(fill="both", expand=True)
    root.update()

    class WheelEvent:
        def __init__(self, delta: int) -> None:
            self.delta = delta

    scroller = table._scroll_controller
    assert scroller.scroll_x == 0.0
    assert scroller.scroll_y == 0.0

    # Wheel down scrolls the body, and wheel up cannot go above the first row
    scroller._on_mousewheel_v(WheelEvent(-120))
    assert scroller.scroll_y > 0.0
    scroller._on_mousewheel_v(WheelEvent(120 * 50))
    assert scroller.scroll_y == 0.0

    # Shift+wheel scrolls sideways and cannot go past the left edge
    scroller._on_mousewheel_h(WheelEvent(-120))
    assert scroller.scroll_x > 0.0
    scroller._on_mousewheel_h(WheelEvent(120 * 50))
    assert scroller.scroll_x == 0.0

    # Dragging the vertical scrollbar to the very end stops at the furthest scroll position
    scroller.on_v_scrollbar_command("moveto", "1.0")
    assert scroller.scroll_y == scroller._get_max_scroll_y() > 0.0
    scroller.on_v_scrollbar_command("scroll", "-1", "pages")
    assert 0.0 < scroller.scroll_y < scroller._get_max_scroll_y()

    # Dragging the horizontal scrollbar to the very end stops at the furthest scroll position
    scroller.on_h_scrollbar_command("moveto", "1.0")
    assert scroller.scroll_x == scroller._get_max_scroll_x() > 0.0

    # Deleting rows near the end pulls the view back so no blank space shows below the last row
    table.delete_rows(list(range(100, 200)))
    root.update()
    assert scroller.scroll_y == scroller._get_max_scroll_y()

    # scroll_to brings a far-away row into view, and replacing the data returns to the top
    table.scroll_to(row=0)
    assert scroller.scroll_y == 0.0
    table.scroll_to(row=99)
    assert scroller.scroll_y == scroller._get_max_scroll_y()
    table.configure(values=[[f"{r}-{c}" for c in range(6)] for r in range(50)])
    assert scroller.scroll_y == 0.0

    table.destroy()
    root.destroy()


def test_style_reconfigure_theme_defaults_and_appearance_mode() -> None:
    """Verify style options reconfigure live, None restores theme defaults, and colors follow appearance mode."""
    root = ctk.CTk()
    root.geometry("800x500+9999+9999")
    previous_mode = ctk.get_appearance_mode()

    table = CTkTable(
        root,
        headers=["ID", "Name", "Status"],
        values=[[1, "Alice", "Active"], [2, "Bob", "Inactive"]],
        text_color=("#111111", "#eeeeee"),
    )
    table.pack(fill="both", expand=True)
    root.update()

    try:
        # Colors follow the appearance mode through the widget's own callback
        ctk.set_appearance_mode("Dark")
        table._set_appearance_mode("Dark")
        assert table._style.colors["text"] == "#eeeeee"
        ctk.set_appearance_mode("Light")
        table._set_appearance_mode("Light")
        assert table._style.colors["text"] == "#111111"

        # Row colors and per-column fonts update the ready-to-draw caches immediately
        table.configure(row_color="#101010", alternate_row_color="#202020", font={"Name": "bold"})
        assert table._style.colors["row_even"] == "#101010"
        assert table._style.colors["row_odd"] == "#202020"
        assert 1 in table._style.column_fonts
        assert table.cget("row_color") == "#101010"

        # Passing None puts the theme default back instead of storing None
        theme = ctk.ThemeManager.theme
        table.configure(text_color=None, selected_color=None, selected_text_color=None, font=None)
        assert table.cget("text_color") == theme["CTkLabel"]["text_color"]
        assert table.cget("selected_color") == theme["CTkButton"]["fg_color"]
        assert table._style.colors["text"]
        assert table._style.colors["selected_bg"]
        assert table._style.colors["selected_text"]
        assert table._style.column_fonts == {}

        # Alignment settings can be replaced and read back, and header_fg_color is readable too
        table.configure(justify={"default": "left", "ID": "right"}, header_alignment="center")
        assert table._style.get_column_alignments() == {0: "right", 1: "left", 2: "left"}
        assert table._style.get_header_alignments() == {0: "center", 1: "center", 2: "center"}
        assert table.cget("header_fg_color")
    finally:
        ctk.set_appearance_mode(previous_mode)
        table.destroy()
        root.destroy()


if __name__ == "__main__":
    run_headless_tests()
    test_theme_color_pair_not_unpacked_as_columns()
    test_column_color_dict_styling()
    test_column_widths_flex_and_auto()
    test_show_headers_visibility()
    test_dictionary_and_partial_headers()
    test_copy_selection_asymmetric_column_and_row_lengths()
    test_show_columns_visibility_and_interaction()
    test_named_header_keys_scoped_attributes()
    test_keyboard_navigation_and_shortcuts()
    test_divider_drag_resizes_column_left_of_divider()
    test_scroll_wheel_scrollbars_and_clamping()
    test_style_reconfigure_theme_defaults_and_appearance_mode()
