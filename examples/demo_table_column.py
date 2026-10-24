"""Demo of per-column styling, column visibility toggling, and header customization in CTkTable.

Demonstrates:
  - Scoped column attributes configured via header titles and numeric indices.
  - Custom fonts and colors per column (e.g. bold green currency values).
  - Independent alignment for body columns and header titles.
  - Dynamic column visibility toggling (show_columns).
  - Header hover highlights on sortable columns.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from typing import Any

import customtkinter as ctk

from ctkforge import CTkTable

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CTkTable - Per-Column Styling & Column Visibility Demo")
app.geometry("860x520")
app.minsize(700, 380)

# Sample tabular dataset
headers = ["ID", "Employee Name", "Department", "Salary (£)", "Status"]
values: list[list[Any]] = [
    [101, "Ada Lovelace", "Research", "£125,000", "Active"],
    [102, "Alan Turing", "Data Systems", "£135,000", "Active"],
    [103, "Grace Hopper", "Engineering", "£130,000", "On Leave"],
    [104, "Claude Shannon", "Information Theory", "£140,000", "Active"],
    [105, "Margaret Hamilton", "Infrastructure", "£138,000", "Active"],
    [106, "John von Neumann", "Applied Math", "£145,000", "Probation"],
    [107, "Donald Knuth", "Algorithms", "£150,000", "Active"],
    [108, "Katherine Johnson", "Orbital Mechanics", "£142,000", "Active"],
    [109, "Dennis Ritchie", "Systems Architecture", "£148,000", "Inactive"],
    [110, "Ken Thompson", "Core Computing", "£146,000", "Active"],
    [111, "Barbara Liskov", "Methodology", "£144,000", "Active"],
    [112, "Edsger Dijkstra", "Formal Methods", "£139,000", "Active"],
]

# Control toolbar for dynamic visibility toggling
toolbar = ctk.CTkFrame(app, fg_color="transparent")
toolbar.pack(fill="x", padx=20, pady=(15, 0))

# Configure table with per-column styling using both header titles and column indices
table = CTkTable(
    app,
    headers=headers,
    values=values,
    column_widths={"default": "auto", "ID": 70, "Employee Name": 180, 2: 170, "Salary (£)": 130},
    sort_key={"ID": "int", "Salary (£)": "str"},
    justify={
        "default": "left",
        "ID": "center",
        "Salary (£)": "right",
        "Status": "center",
    },
    font={
        "Department": "bold",
    },
    text_color={
        "Salary (£)": ("#1b7a37", "#2ecc71"),  # Forest green (light) / emerald (dark)
        "Status": ("#8a6d00", "#f1c40f"),  # Golden amber (light/dark)
    },
    header_alignment={
        "default": "left",
        "ID": "center",
        "Salary (£)": "right",
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

table.pack(fill="both", expand=True, padx=20, pady=(10, 20))


def toggle_dept_visibility() -> None:
    """Toggle visibility of the department column using header title."""
    is_visible = dept_switch.get() == 1
    table.configure(show_columns={"Department": is_visible})


dept_switch = ctk.CTkSwitch(
    toolbar,
    text="Show Department",
    command=toggle_dept_visibility,
)
dept_switch.select()
dept_switch.pack(side="left", padx=(0, 15))


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    app.mainloop()
