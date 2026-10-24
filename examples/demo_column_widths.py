"""Demo demonstrating column_widths behavior with 3 columns in CTkTable.

Shows how explicit widths behave when canvas is wider than the sum of columns
(auto-stretching the final column) vs when resized smaller (horizontal scroll).

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from typing import Any

import customtkinter as ctk

from ctkforge import CTkTable

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CTkTable - Column Widths Demo (3 Columns)")
app.geometry("700x320")
app.minsize(350, 220)

headers = ["ID", "Employee Name", "Role"]
values: list[list[Any]] = [
    ["EMP-101", "Ada Lovelace", "Mathematician"],
    ["EMP-102", "Alan Turing", "Cryptanalyst"],
    ["EMP-103", "Grace Hopper", "Computer Scientist"],
    ["EMP-104", "Claude Shannon", "Information Theorist"],
    ["EMP-105", "Margaret Hamilton", "Software Engineer"],
]

# Column widths configured via dictionary:
# Column 0 = 100px (fixed ID)
# Column 1 = "auto" (default fallback, Employee Name absorbs remaining flex space)
# Column 2 = 150px (fixed Role)
table = CTkTable(
    app,
    headers=headers,
    values=values,
    column_widths={"default": "auto", 0: 100, 2: 150},
    selection_mode="single",
    row_height=30,
    header_height=32,
)
table.pack(fill="both", expand=True, padx=20, pady=20)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    app.mainloop()
