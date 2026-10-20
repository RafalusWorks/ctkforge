"""Basic demo for CTkPopup. Just a simple window, a button, and a popup."""

from __future__ import annotations

import customtkinter as ctk

from ctkforge import CTkPopup


def show_popup(parent: ctk.CTk) -> bool:
    """Open a modal confirmation popup and return user choice."""
    popup = CTkPopup(
        master=parent,
        title="Curiosity Alert",
        text="You clicked the button!\n\nDo you want to proceed with this action?",
        preset="question",
        sound=True,
    )
    # .get() blocks until the user clicks a button or dismisses the window
    return bool(popup.get())


def main() -> None:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("CTkPopup - Basic Demo")
    app.geometry("440x220")
    app.minsize(380, 180)

    # Clean shutdown protocol
    def on_closing() -> None:
        """Stop the event loop immediately and destroy window resources."""
        app.quit()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # UI Widgets
    title_label = ctk.CTkLabel(
        app,
        text="CTkPopup Basic Demo",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    title_label.pack(pady=(24, 8))

    status_label = ctk.CTkLabel(
        app,
        text="Click the button to open the popup",
        font=ctk.CTkFont(size=12),
        text_color="gray70",
    )

    # Button click handler calling the popup function
    def on_button_click() -> None:
        user_agreed = show_popup(parent=app)

        if user_agreed:
            status_label.configure(
                text="Result: You clicked Yes!",
                text_color="#34D399",
            )
        else:
            status_label.configure(
                text="Result: You clicked No or closed the dialog.",
                text_color="#F87171",
            )

    btn = ctk.CTkButton(
        app,
        text="Open Popup",
        font=ctk.CTkFont(size=14, weight="bold"),
        height=40,
        command=on_button_click,
    )
    btn.pack(pady=10, padx=40, fill="x")
    status_label.pack(pady=(4, 20))

    app.mainloop()


if __name__ == "__main__":
    main()
