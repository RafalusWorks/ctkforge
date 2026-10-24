"""Demo of advanced CRUD and clipboard features in CTkTable.

Shows how to manage large tabular datasets in CustomTkinter:
  - Rendering and scrolling high-volume transaction grids.
  - Adding, editing, and deleting table rows in place.
  - Exporting selected cells and rows to the clipboard as TSV.
  - Sorting formatted data columns like currency and timestamps.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

import tkinter as tk
from datetime import datetime, timedelta
from typing import Any, Final

import customtkinter as ctk

from ctkforge import CTkTable

# Application Metadata & Constants
APPLICATION_NAME: Final[str] = "CTkTable"
APPLICATION_VERSION: Final[str] = "0.5.0"
APPLICATION_TAGLINE: Final[str] = "Clipboard, Selection & CRUD (Phase 5)"
APPLICATION_WINDOW_TITLE: Final[str] = f"{APPLICATION_NAME} v{APPLICATION_VERSION} - {APPLICATION_TAGLINE}"

BASE_WINDOW_WIDTH: Final[int] = 1100
BASE_WINDOW_HEIGHT: Final[int] = 720
BASE_MIN_WINDOW_WIDTH: Final[int] = 800
BASE_MIN_WINDOW_HEIGHT: Final[int] = 500

TABLE_HEADERS: Final[list[str]] = [
    "Transaction ID",
    "Date & Time",
    "Customer Name",
    "Customer Email",
    "Category",
    "Product SKU",
    "Quantity",
    "Unit Price",
    "Total Amount",
    "Status",
]

COLUMN_WIDTHS: Final[dict[int | str, int | str]] = {
    "default": "auto",
    0: 130,  # Transaction ID
    1: 150,  # Date & Time
    2: 160,  # Customer Name
    3: 210,  # Customer Email
    4: 150,  # Category
    5: 130,  # Product SKU
    6: 80,  # Quantity
    7: 100,  # Unit Price
    8: 120,  # Total Amount
    9: 110,  # Status
}

TABLE_SORT_KEY: Final[dict[int | str, str]] = {
    "default": "str",
    1: "date",
    6: "int",
    7: "float",
    8: "float",
}


def parse_currency(val: Any) -> float:
    """Extract numeric float from formatted currency strings like '£1,420.50'."""
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = "".join(ch for ch in str(val) if ch.isdigit() or ch in ".-")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def generate_mock_data(row_count: int) -> list[list[Any]]:
    """Generate wide transaction records for table testing."""
    customers = [
        ("Emma Watson", "e.watson@enterprise.io"),
        ("Liam Neeson", "l.neeson@taken.com"),
        ("Olivia Colman", "o.colman@crown.co.uk"),
        ("Noah Centineo", "n.centineo@hollywood.com"),
        ("Sophia Loren", "s.loren@cinema.it"),
        ("James Bond", "007@mi6.gov.uk"),
        ("Mia Farrow", "m.farrow@broadway.org"),
        ("Benjamin Button", "b.button@curious.com"),
        ("Charlotte Bronte", "c.bronte@literature.ac.uk"),
        ("Lucas Skywalker", "l.skywalker@rebelalliance.net"),
        ("Amelia Earhart", "a.earhart@aviation.aero"),
        ("Henry Cavill", "h.cavill@witcher.net"),
    ]
    categories = [
        "Hardware",
        "Enterprise Cloud",
        "Software License",
        "DevOps Support",
        "Consulting",
        "Network Security",
        "Data Pipeline",
        "AI Compute",
    ]
    statuses = ["Completed", "Pending", "Processing", "Shipped", "Verified"]

    base_time = datetime(2026, 1, 1, 9, 0, 0)
    data: list[list[Any]] = []

    for i in range(1, row_count + 1):
        txn_id = f"TXN-{100000 + i}"
        txn_time = (base_time + timedelta(minutes=i * 7)).strftime("%Y-%m-%d %H:%M")
        customer_name, customer_email = customers[i % len(customers)]
        category = categories[(i * 3) % len(categories)]
        sku = f"SKU-{(i * 17) % 9000 + 1000}"
        qty = (i % 25) + 1
        unit_price = (i * 19.95) % 650 + 15.0
        total_amt = qty * unit_price
        status = statuses[(i * 2) % len(statuses)]

        data.append(
            [
                txn_id,
                txn_time,
                customer_name,
                customer_email,
                category,
                sku,
                qty,
                f"£{unit_price:,.2f}",
                f"£{total_amt:,.2f}",
                status,
            ]
        )
    return data


class TableDemoApp(ctk.CTk):
    """Interactive desktop verification harness for CTkTable Phase 5."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title(APPLICATION_WINDOW_TITLE)
        self.geometry(f"{BASE_WINDOW_WIDTH}x{BASE_WINDOW_HEIGHT}")
        self.minsize(BASE_MIN_WINDOW_WIDTH, BASE_MIN_WINDOW_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Configure root layout
        self.grid_rowconfigure(2, weight=1)  # Table viewport expands
        self.grid_columnconfigure(0, weight=1)

        self._created_rows_count = 0

        self._build_header()
        self._build_toolbar()
        self._build_table_viewport()
        self._build_clipboard_preview_bar()
        self._build_status_bar()

    def _build_header(self) -> None:
        """Create the standardized top-left header bar."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text=APPLICATION_NAME,
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.pack(side="left", padx=(0, 6))

        separator_label = ctk.CTkLabel(
            header_frame,
            text="-",
            font=ctk.CTkFont(size=14),
            text_color="gray60",
        )
        separator_label.pack(side="left", padx=(0, 6))

        tagline_label = ctk.CTkLabel(
            header_frame,
            text=APPLICATION_TAGLINE,
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="gray70",
        )
        tagline_label.pack(side="left")

    def _build_toolbar(self) -> None:
        """Create controls for CRUD, clipboard, target selection, and appearance."""
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 10))

        # Target selection (Row vs Cell)
        target_label = ctk.CTkLabel(toolbar, text="Select Target:", font=ctk.CTkFont(size=12, weight="bold"))
        target_label.pack(side="left", padx=(0, 5))

        self._target_seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["Row", "Cell"],
            command=self._on_target_changed,
            width=110,
        )
        self._target_seg.set("Row")
        self._target_seg.pack(side="left", padx=(0, 10))

        # CRUD actions
        btn_insert = ctk.CTkButton(
            toolbar,
            text="+ Insert Row",
            width=105,
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._insert_sample_row,
        )
        btn_insert.pack(side="left", padx=(0, 6))

        btn_delete = ctk.CTkButton(
            toolbar,
            text="- Delete Row",
            width=105,
            fg_color="#c62828",
            hover_color="#b71c1c",
            command=self._delete_selected_rows,
        )
        btn_delete.pack(side="left", padx=(0, 6))

        btn_copy = ctk.CTkButton(
            toolbar,
            text="Copy (Ctrl+C)",
            width=110,
            command=self._trigger_copy,
        )
        btn_copy.pack(side="left", padx=(0, 10))

        # Theme toggle
        self._mode_switch = ctk.CTkSwitch(
            toolbar,
            text="Light Mode",
            command=self._toggle_theme,
        )
        self._mode_switch.pack(side="right")

    def _build_table_viewport(self) -> None:
        """Instantiate the CTkTable widget with 50,000 records and Phase 5 features."""
        initial_data = generate_mock_data(50_000)

        # Allow editing on Customer, Email, Category, SKU, Quantity, Unit Price
        editable_cols = {c: True for c in [2, 3, 4, 5, 6, 7]}

        self._table = CTkTable(
            self,
            values=initial_data,
            headers=TABLE_HEADERS,
            column_widths=COLUMN_WIDTHS,
            sort_key=TABLE_SORT_KEY,
            editable=editable_cols,
            on_cell_edit=self._on_cell_edited,
            row_height=28,
            header_height=32,
            selection_target="row",
            selection_mode="extended",
            copyable=True,
            alternate_row_color=("gray92", "gray14"),
            corner_radius=5,
            border_width=1,
            header_sortable={0: False, 1: False},
            command=self._on_table_selection,
        )
        self._table.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 8))

        # User-level keybindings:
        self._table.bind("<F2>", lambda _event: self._table.edit_focused_cell())
        self._table.bind("<Delete>", lambda _event: self._delete_selected_rows())
        self._table.bind("<Control-c>", lambda _event: self._trigger_copy(), add="+")
        self._table.bind("<Control-C>", lambda _event: self._trigger_copy(), add="+")
        self.bind("<Control-c>", lambda _event: self._trigger_copy())
        self.bind("<Control-C>", lambda _event: self._trigger_copy())

        # Right-click context menu:
        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="Copy TSV (Ctrl+C)", command=self._trigger_copy)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Insert Row", command=self._insert_sample_row)
        self._context_menu.add_command(label="Delete Row(s)", command=self._delete_selected_rows)
        self._table.bind("<Button-3>", self._show_context_menu)

    def _build_clipboard_preview_bar(self) -> None:
        """Create a compact clipboard monitor panel showing last copied TSV snippet."""
        clip_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray18"), corner_radius=6)
        clip_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))

        clip_title = ctk.CTkLabel(
            clip_frame,
            text="Clipboard Preview:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray60",
        )
        clip_title.pack(side="left", padx=(10, 8), pady=4)

        self._clip_preview_label = ctk.CTkLabel(
            clip_frame,
            text="(Press Ctrl+C or Right-Click -> Copy to capture TSV)",
            font=ctk.CTkFont(size=11),
            text_color="gray75",
            anchor="w",
        )
        self._clip_preview_label.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=4)

    def _build_status_bar(self) -> None:
        """Create telemetry status bar displaying record counts, selection, and help."""
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 12))

        self._status_label = ctk.CTkLabel(
            status_frame,
            text="Ready. Ctrl+C to Copy | Del to Delete | Double-click or Enter to Edit",
            font=ctk.CTkFont(size=12),
            text_color="gray65",
        )
        self._status_label.pack(side="left")

        scaling_val = self._get_window_scaling() if hasattr(self, "_get_window_scaling") else 1.0
        self._telemetry_label = ctk.CTkLabel(
            status_frame,
            text=f"{len(self._table.get()):,} Records | DPI: {scaling_val * 100:.0f}%",
            font=ctk.CTkFont(size=12),
            text_color="gray55",
        )
        self._telemetry_label.pack(side="right")

    def _update_record_count(self) -> None:
        """Update record count in the status telemetry."""
        scaling_val = self._get_window_scaling() if hasattr(self, "_get_window_scaling") else 1.0
        self._telemetry_label.configure(text=f"{len(self._table.get()):,} Records | DPI: {scaling_val * 100:.0f}%")

    def _show_context_menu(self, event: Any) -> None:
        """Display context menu at mouse cursor with right-click selection."""
        cell = self._table._get_cell_at(event.x, event.y)
        if cell is not None:
            r, c = cell
            if self._table.cget("selection_target") == "cell":
                if (r, c) not in self._table.get_selected_cells():
                    self._table.clear_selection(notify=False)
                    self._table.select_cell(r, c)
            else:
                if r not in self._table.get_selected_rows():
                    self._table.clear_selection(notify=False)
                    self._table.select_row(r)

        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _on_target_changed(self, value: str) -> None:
        """Switch between row and cell selection modes."""
        target = "cell" if value.lower() == "cell" else "row"
        self._table.configure(selection_target=target)
        self._status_label.configure(
            text=f"Switched to {target.title()} selection mode. Select a {target} to begin.",
            text_color="gray65",
        )

    def _on_table_selection(self, selected_items: list[Any]) -> None:
        """Handle selection events from CTkTable."""
        target_name = "rows" if self._table.cget("selection_target") == "row" else "cells"
        self._status_label.configure(
            text=f"Selected: {len(selected_items):,} {target_name} | Del to delete | Ctrl+C to copy",
            text_color="gray65",
        )

    def _on_cell_edited(self, actual_row: int, col: int, old_val: Any, new_val: Any) -> None:
        """Display real-time telemetry when a cell is edited."""
        col_name = TABLE_HEADERS[col] if col < len(TABLE_HEADERS) else f"Col {col}"
        self._status_label.configure(
            text=f"Edited Record #{actual_row + 1} [{col_name}]: '{old_val}' -> '{new_val}' (Committed)",
            text_color="#3b8ed0",
        )
        # Keep Total Amount (col 8) synchronized when Quantity (6) or Unit Price (7) changes
        if col in (6, 7):
            try:
                disp_row = self._table.get_display_row_index(actual_row)
                row_vals = self._table.get_row(disp_row)
                qty = int(row_vals[6])
                price = parse_currency(row_vals[7])
                total = qty * price
                self._table.update_cell(disp_row, 8, f"£{total:,.2f}", notify=False)
            except (ValueError, TypeError, IndexError):
                pass

    def _insert_sample_row(self) -> None:
        """Insert a brand new sample row at the top or after current selection."""
        self._created_rows_count += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_row = [
            f"TXN-NEW{self._created_rows_count:03d}",
            now_str,
            f"VIP Client {self._created_rows_count}",
            f"client{self._created_rows_count}@enterprise.com",
            "Consulting",
            f"SKU-{8000 + self._created_rows_count}",
            2,
            "£250.00",
            "£500.00",
            "Verified",
        ]

        if self._table.cget("selection_target") == "cell":
            selected_cells = self._table.get_selected_cells()
            target_idx = (selected_cells[0][0] + 1) if selected_cells else 0
        else:
            selected_rows = self._table.get_selected_rows()
            target_idx = (selected_rows[0] + 1) if selected_rows else 0

        inserted_disp = self._table.insert_row(target_idx, new_row)
        self._table.clear_selection(notify=False)
        if self._table.cget("selection_target") == "cell":
            self._table.select_cell(inserted_disp, 0)
        else:
            self._table.select_row(inserted_disp)

        self._table.scroll_to(row=inserted_disp)
        self._update_record_count()
        self._status_label.configure(
            text=f"Inserted new row at position #{inserted_disp + 1} (Total: {len(self._table.get()):,})",
            text_color="#4caf50",
        )

    def _delete_selected_rows(self) -> None:
        """Delete currently selected row(s), supporting both row and cell selection modes."""
        if self._table.cget("selection_target") == "cell":
            selected_rows = sorted({r for r, _ in self._table.get_selected_cells()})
        else:
            selected_rows = self._table.get_selected_rows()

        if not selected_rows:
            self._status_label.configure(
                text="No rows selected to delete. Select a row or cell first.",
                text_color="#e53935",
            )
            return

        count = len(selected_rows)
        self._table.delete_rows(selected_rows)
        self._update_record_count()
        self._status_label.configure(
            text=f"Deleted {count:,} row(s). (Remaining: {len(self._table.get()):,})",
            text_color="#e53935",
        )

    def _trigger_copy(self) -> None:
        """Trigger copy_selection and display copied snippet in preview bar."""
        tsv = self._table.copy_selection()
        if tsv:
            first_line = tsv.splitlines()[0]
            line_count = len(tsv.splitlines())
            display_snippet = first_line if len(first_line) < 70 else f"{first_line[:70]}..."
            suffix = f" (+{line_count - 1} more lines)" if line_count > 1 else ""
            self._clip_preview_label.configure(
                text=f'Copied {line_count:,} line(s) to Clipboard: "{display_snippet}"{suffix}',
                text_color="#4caf50",
            )
        else:
            self._clip_preview_label.configure(
                text="Nothing copied. Make a selection first.",
                text_color="gray60",
            )

    def _toggle_theme(self) -> None:
        """Toggle between Dark and Light appearance modes."""
        if self._mode_switch.get() == 1:
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    def _on_closing(self) -> None:
        """Stop the event loop immediately and destroy window resources."""
        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = TableDemoApp()
    app.mainloop()
