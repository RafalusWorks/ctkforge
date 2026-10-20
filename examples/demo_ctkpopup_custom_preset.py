"""Demonstration of creating and using custom presets in CTkPopup."""

from __future__ import annotations

import customtkinter as ctk

from ctkforge import CTkPopup

# Register a custom preset application-wide
CTkPopup.PRESETS["my_custom_preset"] = {
    "title": "Unsaved Changes",
    "icon": "images/custom_star.png",
    "buttons": [
        {"text": "Save & Exit", "value": "save", "role": "primary"},
        {"text": "Discard", "value": "discard", "role": "destructive"},
        {"text": "Keep Editing", "value": "cancel", "role": "cancel"},
    ],
    "default_button": "save",
    "cancel_button": "cancel",
}


def show_popup(parent: ctk.CTk) -> str | None:
    """Launch the custom preset popup and return the action token."""
    popup = CTkPopup(
        master=parent,
        text="You have unsaved changes in your document.\nWhat would you like to do before closing?",
        preset="my_custom_preset",
        sound=True,
    )
    # .get() returns "save", "discard", or "cancel"
    return popup.get()


def main() -> None:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("CTkPopup - Custom Preset Demo")
    app.geometry("460x230")
    app.minsize(400, 190)

    # Clean shutdown protocol
    def on_closing() -> None:
        """Stop the event loop immediately and destroy window resources."""
        app.quit()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # UI Widgets
    title_label = ctk.CTkLabel(
        app,
        text="Custom Preset Demonstration",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    title_label.pack(pady=(24, 8))

    status_label = ctk.CTkLabel(
        app,
        text="Click above to open the custom preset popup dialog",
        font=ctk.CTkFont(size=12),
        text_color="gray70",
    )

    # Button click handler
    def on_button_click() -> None:
        action = show_popup(parent=app)

        if action == "save":
            status_label.configure(
                text="Result: Saving file and exiting...",
                text_color="#34D399",
            )
        elif action == "discard":
            status_label.configure(
                text="Result: Changes discarded.",
                text_color="#F87171",
            )
        else:
            status_label.configure(
                text="Result: Cancelled. Continuing session.",
                text_color="#60A5FA",
            )

    btn = ctk.CTkButton(
        app,
        text="Click Me",
        font=ctk.CTkFont(size=14, weight="bold"),
        height=40,
        command=on_button_click,
    )
    btn.pack(pady=10, padx=40, fill="x")
    status_label.pack(pady=(4, 20))

    app.mainloop()


if __name__ == "__main__":
    main()
