"""Demo of per-column styling, independent header formatting, and header hover in CTkTable.

Demonstrates:
  - Custom fonts and colors per column (e.g. bold green currency values).
  - Independent alignment for body columns and header titles (e.g. right-aligned numbers).
  - Dynamic header hover highlights on sortable columns.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from typing import Any

import customtkinter as ctk

from ctkforge import CTkTable

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CTkTable - Per-Column Styling & Header Hover Demo")
app.geometry("820x450")
app.minsize(680, 340)

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

# Configure table with per-column styling, custom header formatting, and hover tint
table = CTkTable(
    app,
    headers=headers,
    values=values,
    column_widths=[70, 180, 170, 130],
    sort_key={0: "int", 3: "str"},
    justify={
        "default": "left",
        0: "center",
        3: "right",
        4: "center",
    },
    font={
        2: "bold",
    },
    text_color={
        3: ("#1b7a37", "#2ecc71"),  # Forest green (light) / emerald (dark) for salary
        4: ("#8a6d00", "#f1c40f"),  # Golden amber (light/dark) for status
    },
    header_alignment={
        "default": "left",
        0: "center",
        3: "right",
        4: "center",
    },
    header_text_color={
        3: ("#1f538d", "#3a7ebf"),
    },
    header_font={
        3: ("Segoe UI", 13, "bold"),
    },
    # Interactive hover tint highlighting sortable column headers
    header_hover_color=("#3a7ebf", "#1f538d"),
    header_sortable={3: False},  # Column 3 is not sortable; all others remain sortable
    # Layout and interactivity options
    row_height=30,
    header_height=32,
    corner_radius=6,
    border_width=1,
    selection_target="row",
    selection_mode="single",
    editable={"default": True, 0: False, 1: False, 2: False},
)

table.pack(fill="both", expand=True, padx=20, pady=20)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    app.mainloop()
