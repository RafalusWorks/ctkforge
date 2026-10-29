"""Demo of per-column styling, column visibility toggling, and header customization in CTkTable.

Demonstrates:
  - Scoped column attributes configured via header titles and numeric indices.
  - Custom fonts and colors per column (e.g. bold green currency values).
  - Independent alignment for body columns and header titles.
  - Dynamic column visibility toggling (show_columns).
  - Individual cell text color overrides and dynamic toggle (Status highlights: Inactive/Probation in red, On Leave in orange).
  - Header hover highlights on sortable columns.
  - Dynamic switching between row and cell selection targets.
  - Dynamic switching between single and extended selection modes.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from typing import Any

import customtkinter as ctk

from ctkforge import CTkTable

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CTkTable - Styling & Column Visibility Demo")
app.geometry("1100x580")
app.minsize(850, 380)


# Sample tabular dataset
headers = ["ID", "Employee Name", "Department", "Salary (£)", "Progress", "Status"]
values: list[list[Any]] = [
    [101, "Ada Lovelace", "Research", "£125,000", 95, "Active"],
    [102, "Alan Turing", "Data Systems", "£135,000", 80, "Active"],
    [103, "Grace Hopper", "Engineering", "£130,000", 50, "On Leave"],
    [104, "Claude Shannon", "Information Theory", "£140,000", 85, "Active"],
    [105, "Margaret Hamilton", "Infrastructure", "£138,000", 90, "Active"],
    [106, "John von Neumann", "Applied Math", "£145,000", 40, "Probation"],
    [107, "Donald Knuth", "Algorithms", "£150,000", 100, "Active"],
    [108, "Katherine Johnson", "Orbital Mechanics", "£142,000", 75, "Active"],
    [109, "Dennis Ritchie", "Systems Architecture", "£148,000", 20, "Inactive"],
    [110, "Ken Thompson", "Core Computing", "£146,000", 88, "Active"],
    [111, "Barbara Liskov", "Methodology", "£144,000", 92, "Active"],
    [112, "Edsger Dijkstra", "Formal Methods", "£139,000", 65, "Active"],
]


def _format_progress(value: Any) -> str:
    """Format numeric progress into a block-shaded bar with percentage."""
    filled = min(10, max(0, int(value) // 10))
    return f"[{'█' * filled}{'░' * (10 - filled)}] {int(value):>3}%"


# Configure table with per-column styling using both header titles and column indices
table = CTkTable(
    app,
    headers=headers,
    values=values,
    column_widths={
        "default": "auto",
        "ID": 70,
        "Employee Name": 180,
        2: 170,
        "Salary (£)": 120,
        "Progress": 150,
    },
    sort_key={"ID": "int", "Salary (£)": "str", "Progress": "int"},
    formatters={
        "Progress": _format_progress,
    },
    justify={
        "default": "left",
        "ID": "center",
        "Salary (£)": "right",
        "Progress": "center",
        "Status": "center",
    },
    font={
        "Department": "bold",
        "Progress": ("Consolas", 12),
    },
    text_color={
        "Salary (£)": ("#1b7a37", "#2ecc71"),  # Forest green (light) / emerald (dark)
        "Status": ("#8a6d00", "#f1c40f"),  # Golden amber (light/dark)
    },
    header_alignment={
        "default": "left",
        "ID": "center",
        "Salary (£)": "right",
        "Progress": "center",
        "Status": "center",
    },
    header_text_color={
        "Salary (£)": ("#1f538d", "#3a7ebf"),
    },
    header_font={
        "Salary (£)": ("Segoe UI", 13, "bold"),
    },
    header_hover_color=("#3a7ebf", "#1f538d"),
    header_sortable={"Salary (£)": False},
    show_columns={"default": True},
    row_height=30,
    header_height=32,
    corner_radius=6,
    border_width=1,
    selection_target="row",
    selection_mode="single",
    editable={"default": True, "ID": False, "Employee Name": False, "Department": False},
)

# Status cell highlight color palette
status_colors: dict[str, tuple[str, str]] = {
    "Inactive": ("#c0392b", "#e74c3c"),
    "Probation": ("#c0392b", "#e74c3c"),
    "On Leave": ("#d35400", "#e67e22"),
}


def apply_status_highlights() -> None:
    """Apply individual cell text colors to highlight non-active employee statuses and names."""
    total_rows = len(table.get())
    for row_idx in range(total_rows):
        status_val = str(table.get_cell(row_idx, "Status"))
        if status_val in status_colors:
            color = status_colors[status_val]
            table.set_cell_text_color(row_idx, "Status", color, redraw=False)
            table.set_cell_text_color(row_idx, "Employee Name", color, redraw=False)
    table._redraw()


def toggle_status_highlights() -> None:
    """Toggle individual cell text coloring on or off for the Status column."""
    if status_switch.get() == 1:
        apply_status_highlights()
    else:
        table.clear_cell_text_colors()


def toggle_header_visibility() -> None:
    """Toggle visibility of the pinned table header."""
    is_visible = header_switch.get() == 1
    table.configure(show_headers=is_visible)


def toggle_progress_visibility() -> None:
    """Toggle visibility of the progress column using header title."""
    is_visible = progress_vis_switch.get() == 1
    table.configure(show_columns={"Progress": is_visible})


def toggle_progress_format() -> None:
    """Toggle visual progress bar formatting on or off."""
    if progress_switch.get() == 1:
        table.set_column_formatter("Progress", _format_progress)
    else:
        table.set_column_formatter("Progress", None)


def toggle_alternate_row_color() -> None:
    """Toggle zebra striping / alternate row background coloring."""
    if alt_row_switch.get() == 1:
        table.configure(alternate_row_color=("gray92", "gray14"))
    else:
        table.configure(alternate_row_color=None)


def toggle_selection_target() -> None:
    """Toggle selection target between row and cell mode."""
    target = "cell" if selection_target_switch.get() == 1 else "row"
    selection_target_switch.configure(text=f"Selection: {target.capitalize()}")
    table.configure(selection_target=target)


def toggle_selection_mode() -> None:
    """Toggle selection mode between single and extended."""
    mode = "extended" if selection_mode_switch.get() == 1 else "single"
    selection_mode_switch.configure(text=f"Mode: {mode.capitalize()}")
    table.configure(selection_mode=mode)


# Left sidebar controls
controls_frame = ctk.CTkFrame(app, fg_color="transparent")
controls_frame.pack(side="left", fill="y", padx=(20, 10), pady=20, anchor="n")

header_switch = ctk.CTkSwitch(
    controls_frame,
    text="Show Header",
    command=toggle_header_visibility,
)
header_switch.pack(anchor="w", pady=(0, 15))
header_switch.select()

progress_vis_switch = ctk.CTkSwitch(
    controls_frame,
    text="Show Column",
    command=toggle_progress_visibility,
)
progress_vis_switch.pack(anchor="w", pady=(0, 15))
progress_vis_switch.select()

progress_switch = ctk.CTkSwitch(
    controls_frame,
    text="Custom Formatter",
    command=toggle_progress_format,
)
progress_switch.pack(anchor="w", pady=(0, 15))
progress_switch.select()

alt_row_switch = ctk.CTkSwitch(
    controls_frame,
    text="Alternate Row Color",
    command=toggle_alternate_row_color,
)
alt_row_switch.pack(anchor="w", pady=(0, 15))

status_switch = ctk.CTkSwitch(
    controls_frame,
    text="Cell Text Styling",
    command=toggle_status_highlights,
)
status_switch.pack(anchor="w", pady=(0, 15))
status_switch.select()

selection_target_switch = ctk.CTkSwitch(
    controls_frame,
    text="Selection: Row",
    command=toggle_selection_target,
)
selection_target_switch.pack(anchor="w", pady=(0, 15))

selection_mode_switch = ctk.CTkSwitch(
    controls_frame,
    text="Mode: Single",
    command=toggle_selection_mode,
)
selection_mode_switch.pack(anchor="w", pady=(0, 15))

# Apply initial highlights and pack table
apply_status_highlights()
table.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=20)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    app.mainloop()
