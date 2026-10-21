"""Quick-start example for CTkTable data displays.

Renders a lightweight editable data table with custom headers, row values,
and protected columns to demonstrate in-place cell editing with minimal code.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

import customtkinter as ctk

from ctkforge import CTkTable

app = ctk.CTk()

table = CTkTable(
    app,
    headers=["ID", "Name", "Role", "Salary"],
    values=[
        [1, "Ada Lovelace", "Mathematician", "£120,000"],
        [2, "Alan Turing", "Cryptanalyst", "£135,000"],
        [3, "Grace Hopper", "Computer Scientist", "£130,000"],
    ],
    editable=True,
    editable_columns_exclude=[0],
)
table.pack(fill="both", expand=True, padx=20, pady=20)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
