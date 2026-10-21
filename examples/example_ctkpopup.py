"""Quick-start example for CTkPopup modal dialogs.

Opens a blocking confirmation dialog with the question preset, capturing
the user's boolean choice to update status text in real time.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from __future__ import annotations

import customtkinter as ctk

from ctkforge import CTkPopup

app = ctk.CTk()
app.geometry("420x220")
app.title("CTkPopup Example")

status_label = ctk.CTkLabel(
    app,
    text="Click the button to open a confirmation dialog",
    font=ctk.CTkFont(size=13),
)
status_label.pack(pady=(35, 12))


def show_confirm_dialog() -> None:
    """Open a modal confirmation popup and display the result."""
    popup = CTkPopup(
        master=app,
        title="Confirm Action",
        text="Do you want to proceed with the update?",
        preset="question",
    )

    # .get() synchronously blocks until user chooses an action or dismisses dialog
    choice = popup.get()

    if choice is True:
        status_label.configure(text="Result: User clicked Yes", text_color="#10B981")
    else:
        status_label.configure(
            text="Result: User clicked No or closed the dialog",
            text_color="#EF4444",
        )


btn = ctk.CTkButton(
    app,
    text="Open Confirmation Dialog",
    command=show_confirm_dialog,
    height=36,
)
btn.pack(pady=10)


def on_closing() -> None:
    """Graceful window close protocol.

    Calling root.quit() stops the Tcl event loop immediately, preventing
    Python from hanging inside app.mainloop() when the window is closed.
    """
    app.quit()
    app.destroy()


# Intercept window close ('X' button) to cleanly break mainloop
app.protocol("WM_DELETE_WINDOW", on_closing)

app.mainloop()
