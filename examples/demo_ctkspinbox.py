"""CustomTkinter application featuring a classic stacked spinbox widget."""

from typing import Final

import customtkinter as ctk

from ctkforge import CTkSpinbox

APPLICATION_NAME: Final[str] = "CTkSpinbox Demo"
APPLICATION_VERSION: Final[str] = "0.2.0"
APPLICATION_TAGLINE: Final[str] = "Identify yourself to begin."
APPLICATION_WINDOW_TITLE: Final[str] = f"{APPLICATION_NAME} v{APPLICATION_VERSION}"

BASE_WINDOW_WIDTH: Final[int] = 460
BASE_WINDOW_HEIGHT: Final[int] = 420
BASE_MIN_WINDOW_WIDTH: Final[int] = 420
BASE_MIN_WINDOW_HEIGHT: Final[int] = 380


class WelcomeApp(ctk.CTk):
    """Main application window using modern CustomTkinter components."""

    def __init__(self) -> None:
        super().__init__()

        # Window configuration
        self.title(APPLICATION_WINDOW_TITLE)
        self.geometry(f"{BASE_WINDOW_WIDTH}x{BASE_WINDOW_HEIGHT}")
        self.minsize(BASE_MIN_WINDOW_WIDTH, BASE_MIN_WINDOW_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Theme configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct and layout all UI elements."""
        # Main container card
        self.container = ctk.CTkFrame(self, corner_radius=12)
        self.container.pack(fill="both", expand=True, padx=24, pady=24)

        # Header bar (title and tagline aligned top-left)
        self.header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(16, 20), anchor="w")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=f"{APPLICATION_NAME} -",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.title_label.pack(side="left", padx=(0, 6))

        self.tagline_label = ctk.CTkLabel(
            self.header_frame,
            text=APPLICATION_TAGLINE,
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray70",
        )
        self.tagline_label.pack(side="left")

        # Name input field
        self.name_entry = ctk.CTkEntry(
            self.container,
            placeholder_text="Enter your name...",
            width=280,
            height=36,
        )
        self.name_entry.pack(pady=(0, 14))
        self.name_entry.bind("<Return>", lambda _event: self._handle_greet())
        self.name_entry.focus()

        # Age spinbox input row
        self.spinbox_row = ctk.CTkFrame(self.container, fg_color="transparent")
        self.spinbox_row.pack(pady=(0, 16))

        self.spinbox_label = ctk.CTkLabel(
            self.spinbox_row,
            text="Age:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray80",
        )
        self.spinbox_label.pack(side="left", padx=(0, 10))

        self.age_spinbox = CTkSpinbox(
            self.spinbox_row,
            start_value=25,
            min_value=1,
            max_value=120,
            step=5,
            width=90,
            height=30,
        )
        self.age_spinbox.pack(side="left")

        # Submit button
        self.submit_btn = ctk.CTkButton(
            self.container,
            text="Continue",
            width=280,
            height=36,
            command=self._handle_greet,
        )
        self.submit_btn.pack(pady=(0, 14))

        # Dynamic welcome / feedback label
        self.welcome_label = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=15, weight="bold"),
            wraplength=360,
        )
        self.welcome_label.pack(pady=(6, 6))

    def _handle_greet(self) -> None:
        """Read the input name and age, then update the feedback label."""
        name = self.name_entry.get().strip()
        age = self.age_spinbox.get()

        if not name:
            self.welcome_label.configure(
                text="Please provide a name first.",
                text_color="#f87171",
            )
            return

        self.welcome_label.configure(
            text=f"Welcome, {name} (Age: {age})!",
            text_color="#60a5fa",
        )

    def _on_closing(self) -> None:
        """Gracefully destroy window on close request."""
        self.destroy()


def main() -> None:
    """Initialize and run the application main loop."""
    app = WelcomeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
