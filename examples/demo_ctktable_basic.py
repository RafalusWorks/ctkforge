"""Demo of CTkTable data table widget in CustomTkinter.

Launches a preconfigured data table with custom column widths, alternating
row striping, header sorting, and extended cell selection—providing a clean,
plug-and-play reference for tabular layouts in CustomTkinter.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from typing import Any

import customtkinter as ctk

from ctkforge import CTkTable

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Demo Table Basic")
app.geometry("750x380")
app.minsize(600, 300)

headers = ["ID", "Employee Name", "Department", "Salary"]
values: list[list[Any]] = [
    ["EMP-101", "Ada Lovelace", "Research", "£125,000"],
    ["EMP-102", "Alan Turing", "Data Systems", "£135,000"],
    ["EMP-103", "Grace Hopper", "Engineering", "£130,000"],
    ["EMP-104", "Claude Shannon", "Information Theory", "£140,000"],
    ["EMP-105", "Margaret Hamilton", "Infrastructure", "£138,000"],
    ["EMP-106", "John von Neumann", "Applied Math", "£145,000"],
    ["EMP-107", "Donald Knuth", "Algorithms", "£150,000"],
    ["EMP-108", "Katherine Johnson", "Orbital Mechanics", "£142,000"],
    ["EMP-109", "Dennis Ritchie", "Systems Architecture", "£148,000"],
    ["EMP-110", "Ken Thompson", "Core Computing", "£146,000"],
    ["EMP-111", "Barbara Liskov", "Software Methodology", "£144,000"],
    ["EMP-112", "Edsger Dijkstra", "Formal Verification", "£139,000"],
]


# fmt: off
table = CTkTable(
    app,
    headers=headers,
    values=values,
    column_widths=[90, 200, 180], # Column widths: ID=90px, Name=200px, Dept=180px, Salary auto-fills remaining space
    sort_key={0: "int"},  # Numeric sorting enabled on the ID column
    selection_target="cell",
    selection_mode="extended",  # Row selection mode (extended allows multi-select with Ctrl/Shift)
    row_height=30,
    header_height=30,
    alternate_row_color=("gray92", "gray14"),
    corner_radius=5,
    border_width=1,
    editable={1: True},
    header_sortable={3: False},
)
# fmt: on

table.pack(fill="both", expand=True, padx=20, pady=20)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
