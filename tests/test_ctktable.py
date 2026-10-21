"""Comprehensive test and demonstration script for CTkTable."""

from __future__ import annotations

import sys
import time
from typing import Any

import customtkinter as ctk

from ctkforge.table import CTkTable

DEMO_HEADERS: list[str] = ["ID", "Name", "Department", "Salary (£)", "Status"]
DEMO_TYPES: list[str] = ["int", "str", "str", "int", "str"]
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


def run_table_test_suite(
    table: CTkTable,
    root: ctk.CTk,
    visual: bool = False,
) -> None:
    """Execute all 19 automated tests on a table instance (headless or live in-window)."""

    def step(delay: float = 0.3) -> None:
        if visual:
            root.update()
            time.sleep(delay)

    def clean_slate_reset() -> None:
        """Reset table data, selection, sorting, configuration, and column widths to clean baseline."""
        table._cancel_edit()
        table.clear_selection()
        table.clear_sort()
        table.configure(
            values=[list(r) for r in DEMO_DATA],
            selection_target="row",
            selection_mode="extended",
            editable_columns_exclude=None,
            header_sortable_exclude=None,
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
    print("[1/19] Initial State & Dimensions: PASSED", flush=True)

    # 2. Sort by Salary Ascending (column 3)
    table.sort_by(3, ascending=True)
    step()
    assert table.get_cell(0, 1) == "Charlie Day", (
        "Lowest salary Charlie Day should be row 0"
    )
    assert table.get_cell(7, 1) == "Harriet Tubman", (
        "Highest salary Harriet should be row 7"
    )
    assert table.get_sort_state() == (3, True), "Sort state should be (3, True)"
    print("[2/19] Sort by Salary Ascending: PASSED", flush=True)

    # 3. Sort by Salary Descending (column 3)
    table.sort_by(3, ascending=False)
    step()
    assert table.get_cell(0, 1) == "Harriet Tubman", (
        "Highest salary Harriet should be row 0"
    )
    assert table.get_sort_state() == (3, False), "Sort state should be (3, False)"
    print("[3/19] Sort by Salary Descending: PASSED", flush=True)

    # 4. Clear Sort (Restore initial insertion order)
    table.clear_sort()
    step()
    assert table.get_cell(0, 1) == "Alice Morgan", "Alice should return to row 0"
    assert table.get_sort_state() == (None, True), "Sort state should be cleared"
    print("[4/19] Clear Sort (Restore insertion order): PASSED", flush=True)

    # 5. Row Selection
    table.clear_selection()
    table.select_row(1)
    step()
    assert table.get_selected_rows() == [1], "Row 1 should be selected"
    table.clear_selection()
    step()
    assert table.get_selected_rows() == [], "Selection should be empty"
    print("[5/19] Row Selection: PASSED", flush=True)

    # 6. Range Selection (Rows 1 to 3)
    table._selection_manager.apply_click(1, 0)
    table._selection_manager.apply_click(3, 0, is_shift=True)
    table._redraw()
    step()
    assert set(table.get_selected_rows()) == {1, 2, 3}, "Rows 1-3 should be selected"
    table.clear_selection()
    step()
    print("[6/19] Range Selection: PASSED", flush=True)

    # 7. Select All and Deselect
    table.select_all()
    step()
    assert len(table.get_selected_rows()) == 8, "All 8 rows should be selected"
    table.clear_selection()
    step()
    assert table.get_selected_rows() == [], "Selection should be empty after clear"
    print("[7/19] Select All and Deselect: PASSED", flush=True)

    # 8. In-Place Cell Editing and Commit
    table._start_editing(2, 2)
    assert table.is_editing and table._editor._entry is not None, "Editor failed to spawn on cell (2, 2)"
    step()
    table._editor._entry.delete(0, "end")
    table._editor._entry.insert(0, "Operations")
    step()
    table._commit_edit()
    assert table.get_cell(2, 2) == "Operations", (
        "Cell (2, 2) should update to 'Operations'"
    )
    table.update_cell(2, 2, "Logistics")
    step()
    print("[8/19] In-Place Cell Editing and Commit: PASSED", flush=True)

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
    print("[9/19] In-Place Cell Editing Cancellation: PASSED", flush=True)

    # 10. Locked / Non-Editable Column
    table.configure(editable_columns_exclude=[0])
    table._start_editing(0, 0)
    assert not table.is_editing, "Editing column 0 should be blocked"
    table.configure(editable_columns_exclude=None)
    table.configure(header_sortable_exclude=[0])
    assert not table._is_column_header_sortable(0), "Column 0 should not be sortable"
    table.configure(header_sortable_exclude=None)
    step()
    print("[10/19] Locked / Non-Editable Column: PASSED", flush=True)

    # 11. Selection Modes (Cell vs Row)
    table.configure(selection_target="cell")
    table.select_cell(0, 1)
    step()
    assert table.get_selected_cells() == [(0, 1)], "Cell (0, 1) should be selected"
    table.clear_selection()
    table.configure(selection_target="row")
    step()
    print("[11/19] Selection Modes (Cell vs Row): PASSED", flush=True)

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
    print("[12/19] Dirty Numeric Sorting: PASSED", flush=True)

    # 13. Insert Row with Active Sort
    table.sort_by(3, ascending=True)
    table.insert_row(values=[109, "Zack Morris", "Support", 30000, "Active"])
    step()
    assert table.get_cell(0, 1) == "Zack Morris", (
        "Lowest salary Zack should sort to row 0"
    )
    print("[13/19] Insert Row with Active Sort: PASSED", flush=True)

    # 14. Delete Row
    table.delete_rows(0)
    step()
    assert table.get_cell(0, 1) == "Charlie Day", "Charlie Day should return to row 0"
    table.clear_sort()
    step()
    print("[14/19] Delete Row: PASSED", flush=True)

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
    print("[15/19] Auto-Fit Column & Style Configuration: PASSED", flush=True)

    # 16. Scrolling and Viewport Clamping
    table.configure(
        values=[
            [100 + i, f"Employee {i}", "Dept", 50000 + i * 1000, "Active"]
            for i in range(40)
        ]
    )
    root.update()
    table.scroll_to(row=35)
    step()
    assert table._scroll_y > 0.0, "Viewport should scroll down to row 35"
    table.scroll_to(row=0)
    step()
    assert table._scroll_y == 0.0, "Viewport should scroll back to top"
    print("[16/19] Scrolling and Viewport Clamping: PASSED", flush=True)

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
    print("[17/19] Index Resolution (Display <-> Raw): PASSED", flush=True)

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
    print("[18/19] Atomic Row Update: PASSED", flush=True)

    # 19. Batched Auto-Fit Columns
    table.auto_fit_columns()
    step()
    assert isinstance(table._column_widths, (list, dict)), "Column widths should be populated"
    print("[19/19] Batched Auto-Fit Columns: PASSED", flush=True)

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
        column_types=DEMO_TYPES,
        selection_mode="extended",
        selection_target="row",
    )
    table.pack(fill="both", expand=True)
    root.update()

    run_table_test_suite(table, root, visual=False)

    root.destroy()
    print("All automated checks (19/19) passed successfully!")


def launch_interactive_demo() -> None:
    """Launch interactive window for visual inspection and in-window self-testing."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("CTkTable Interactive Demo")
    root.geometry("860x580")
    root.minsize(600, 400)  # Prevents shrinking smaller than 600x400

    title_label = ctk.CTkLabel(
        root,
        text="CTkTable Verification Demo",
        font=ctk.CTkFont(size=20, weight="bold"),
    )
    title_label.pack(pady=(15, 8))

    status_var = ctk.StringVar(value="Status: Ready. Double-click any cell to edit.")

    table = CTkTable(
        root,
        headers=DEMO_HEADERS,
        values=[list(r) for r in DEMO_DATA],
        editable=True,
        column_types=DEMO_TYPES,
        selection_mode="extended",
        selection_target="row",
        on_cell_edit=lambda r, c, old, new: status_var.set(
            f"Status: Cell ({r}, {c}) edited from '{old}' to '{new}'"
        ),
        command=lambda sel: status_var.set(f"Status: Selected rows: {sel}"),
    )
    table.pack(fill="both", expand=True, padx=20, pady=10)

    ctrl_frame = ctk.CTkFrame(root)
    ctrl_frame.pack(fill="x", padx=20, pady=(0, 10))

    def sort_salary() -> None:
        table.sort_by(3, ascending=True)
        status_var.set("Status: Sorted by Salary ascending.")

    def clear_sort_action() -> None:
        table.clear_sort()
        status_var.set("Status: Sort cleared.")

    ctk.CTkButton(ctrl_frame, text="Sort by Salary", command=sort_salary).pack(
        side="left", padx=5, pady=5
    )
    ctk.CTkButton(ctrl_frame, text="Clear Sort", command=clear_sort_action).pack(
        side="left", padx=5, pady=5
    )
    ctk.CTkButton(
        ctrl_frame,
        text="Select All",
        command=lambda: table.select_all(),
    ).pack(side="left", padx=5, pady=5)
    ctk.CTkButton(
        ctrl_frame,
        text="Clear Selection",
        command=lambda: table.clear_selection(),
    ).pack(side="left", padx=5, pady=5)

    def run_in_window_self_test() -> None:
        status_var.set("Status: Running in-window self-test (19 checks)...")
        btn_self_test.configure(state="disabled")
        root.update()
        try:
            run_table_test_suite(table, root, visual=True)
            status_var.set("Status: All 19 automated checks passed! Table restored.")
        finally:
            btn_self_test.configure(state="normal")

    btn_self_test = ctk.CTkButton(
        ctrl_frame,
        text="Run Self-Test",
        command=run_in_window_self_test,
        fg_color="#2b7a4b",
        hover_color="#1e5c37",
    )
    btn_self_test.pack(side="left", padx=5, pady=5)

    status_bar = ctk.CTkLabel(
        root,
        textvariable=status_var,
        anchor="w",
        font=ctk.CTkFont(size=12),
    )
    status_bar.pack(fill="x", padx=25, pady=(0, 10))

    def on_closing() -> None:
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    if "--test" in sys.argv or "--headless" in sys.argv:
        run_headless_tests()
    else:
        launch_interactive_demo()
