"""Interactive visual showcase and test application for CTkPopup.

Demonstrates:
  1. The 5 core presets (Info, Warning, Error, Question, Success)
  2. The 4 semantic button roles (Primary, Cancel, Destructive, Normal)
  3. Visual height comparison: Short Label (< 300px) vs Copyable CTkTextbox (> 300px)
  4. Non-blocking asynchronous callback demonstration
  5. Multi-button custom prompts (Keep Both / Overwrite / Cancel)
  6. Live Light/Dark mode theme toggling
"""

import customtkinter as ctk

from ctkforge import CTkPopup, enable_debug_mode

SAMPLE_TRACEBACK = """Traceback (most recent call last):
  File "C:\\Projects\\App\\database\\engine.py", line 142, in connect
    connection = pool.acquire(timeout=5.0)
  File "C:\\Projects\\App\\.venv\\Lib\\site-packages\\asyncpg\\pool.py", line 482, in acquire
    raise exceptions.PoolTimeoutError("connection acquisition timed out after 5.0s")
asyncpg.exceptions.PoolTimeoutError: connection acquisition timed out after 5.0s

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\\Projects\\App\\main.py", line 88, in handle_request
    data = await db.fetch_all("SELECT * FROM critical_records")
  File "C:\\Projects\\App\\database\\service.py", line 32, in fetch_all
    raise DatabaseConnectionRefusedError("Failed to reach primary database cluster at 10.0.4.12:5432")
app.exceptions.DatabaseConnectionRefusedError: Failed to reach primary database cluster at 10.0.4.12:5432"""


# Application Window Dimensions & Timing
APP_INITIAL_WIDTH: int = 780
APP_INITIAL_HEIGHT: int = 620
APP_MIN_WIDTH: int = 680
APP_MIN_HEIGHT: int = 520
DELAY_TIME_SECONDS: int = 5


class DemoApp(ctk.CTk):
    """Main interactive showcase window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("CTkPopup Feature Showcase & Visual Testing")
        self.geometry(f"{APP_INITIAL_WIDTH}x{APP_INITIAL_HEIGHT}")
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)

        # Graceful close protocol: quit() breaks Tcl event loop so Python doesn't hang in mainloop
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="CTkPopup Interactive Test Suite",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Theme toggle switch
        self.theme_switch = ctk.CTkSwitch(
            header,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="Dark",
            offvalue="Light",
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=0, column=1, sticky="e")

        # Main content scrollable container
        container = ctk.CTkScrollableFrame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        container.grid_columnconfigure((0, 1), weight=1)

        # Section 1: Presets
        self._add_section_header(
            container, "1. Core Presets (The Single CTkPopup Habit)", row=0
        )

        ctk.CTkButton(
            container,
            text="Show Info",
            command=lambda: self._log(
                CTkPopup(
                    master=self,
                    title="Update Available",
                    text="A new version of the software is ready to download.",
                    preset="info",
                ).get()
            ),
        ).grid(row=1, column=0, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="Show Warning",
            command=lambda: self._log(
                CTkPopup(
                    master=self,
                    title="Low Disk Space",
                    text="Your primary SSD has less than 2 GB remaining.",
                    preset="warning",
                ).get()
            ),
        ).grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="Show Error",
            command=lambda: self._log(
                CTkPopup(
                    master=self,
                    title="Network Timeout",
                    text="Failed to connect to the authentication server.",
                    preset="error",
                ).get()
            ),
        ).grid(row=2, column=0, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="Ask Question (Yes/No)",
            command=lambda: self._log(
                CTkPopup(
                    master=self,
                    title="Confirm Overwrite",
                    text="A file with this name already exists. Overwrite it?",
                    preset="question",
                ).get()
            ),
        ).grid(row=2, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="Show Success",
            command=lambda: self._log(
                CTkPopup(
                    master=self,
                    title="Export Complete",
                    text="All 1,420 rows exported to CSV successfully.",
                    preset="success",
                ).get()
            ),
        ).grid(row=3, column=0, padx=10, pady=6, sticky="ew")

        # Section 2: Semantic Roles & Custom Buttons
        self._add_section_header(
            container, "2. Semantic Roles & Custom Button Lists", row=4
        )

        ctk.CTkButton(
            container,
            text="Destructive Action (Danger Red)",
            command=self._test_destructive,
        ).grid(row=5, column=0, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="3-Button File Conflict (Keep Both / Overwrite / Cancel)",
            command=self._test_three_buttons,
        ).grid(row=5, column=1, padx=10, pady=6, sticky="ew")

        # Section 3: Visual Height Calibration (300px Threshold Test)
        self._add_section_header(
            container, "3. Visual Height Calibration (300px Rule)", row=6
        )

        ctk.CTkButton(
            container,
            text="Short Message (< 300px: Clean CTkLabel)",
            command=self._test_short_message,
        ).grid(row=7, column=0, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text="Long Message (> 300px: Copyable CTkTextbox)",
            command=self._test_long_traceback,
        ).grid(row=7, column=1, padx=10, pady=6, sticky="ew")

        # Section 4: Asynchronous & Delayed Screen Centering Tests
        self._add_section_header(
            container, "4. Async Mode & Delayed Screen Centering", row=8
        )

        ctk.CTkButton(
            container,
            text="Launch Non-Blocking Async",
            command=self._test_async_callback,
        ).grid(row=9, column=0, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(
            container,
            text=f"Launch Delayed Popup ({DELAY_TIME_SECONDS}s)",
            command=self._test_delayed_popup,
            fg_color=("#D97706", "#B45309"),
            hover_color=("#B45309", "#92400E"),
        ).grid(row=9, column=1, padx=10, pady=6, sticky="ew")

        # Footer Status Log
        footer = ctk.CTkFrame(self, height=48)
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(6, 20))
        footer.grid_columnconfigure(1, weight=1)

        status_title = ctk.CTkLabel(
            footer, text="Last Return Value:", font=ctk.CTkFont(weight="bold")
        )
        status_title.grid(row=0, column=0, padx=(16, 8), pady=12)

        self.status_display = ctk.CTkLabel(
            footer,
            text="None (Click any button above to test)",
            text_color=("gray30", "gray70"),
        )
        self.status_display.grid(row=0, column=1, sticky="w", padx=8, pady=12)

    def _add_section_header(self, parent: ctk.CTkFrame, title: str, row: int) -> None:
        """Helper to create a visually distinct section divider."""
        header = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80"),
        )
        header.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(16, 8))

    def _toggle_theme(self) -> None:
        """Switch CustomTkinter appearance mode."""
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    def _log(self, value: object) -> None:
        """Update status bar with the clicked return value."""
        self.status_display.configure(
            text=f"{value!r}  (type: {type(value).__name__})",
            text_color=("#2563EB", "#60A5FA"),
        )

    def _test_destructive(self) -> None:
        """Demonstrate dangerous action with warning red styling."""
        popup = CTkPopup(
            master=self,
            title="Delete Database Record",
            text="Are you sure you want to permanently delete this customer record? This operation cannot be undone.",
            icon="warning",
            buttons=[
                {
                    "text": "Delete Permanently",
                    "value": "deleted",
                    "role": "destructive",
                },
                {"text": "Cancel", "value": "cancelled", "role": "cancel"},
            ],
            cancel_button="cancelled",
        )
        self._log(popup.get())

    def _test_three_buttons(self) -> None:
        """Demonstrate 3-button file conflict with distinct semantic roles."""
        popup = CTkPopup(
            master=self,
            title="File Already Exists",
            text="A file named 'report_october.docx' already exists in this folder. What would you like to do?",
            icon="warning",
            buttons=[
                {"text": "Keep Both", "value": "rename", "role": "primary"},
                {"text": "Overwrite", "value": "overwrite", "role": "destructive"},
                {"text": "Cancel", "value": False, "role": "cancel"},
            ],
            cancel_button=False,
        )
        self._log(popup.get())

    def _test_short_message(self) -> None:
        """Demonstrate standard height message rendered in CTkLabel."""
        text = (
            "This is a standard multi-line notice.\n\n"
            "It easily fits under the 300px ceiling, so it renders cleanly "
            "as a centered, lightweight text label without scrollbars."
        )
        popup = CTkPopup(
            master=self, title="Short Message Test", text=text, preset="info"
        )
        self._log(popup.get())

    def _test_long_traceback(self) -> None:
        """Demonstrate long exception text switching to a scrollable, copyable CTkTextbox."""
        popup = CTkPopup(
            master=self,
            title="Unhandled Exception Detected",
            text=SAMPLE_TRACEBACK,
            preset="error",
            buttons=[
                {"text": "Copy & Dismiss", "value": "dismiss", "role": "primary"},
            ],
            width=520,
        )
        self._log(popup.get())

    def _test_async_callback(self) -> None:
        """Demonstrate non-blocking callback execution."""

        def handle_async_result(val: object) -> None:
            self._log(f"Async Callback Received: {val}")

        CTkPopup(
            master=self,
            title="Non-Blocking Mode",
            text="This popup does not freeze Python script execution. It uses callback=handler to process the choice asynchronously.",
            preset="info",
            callback=handle_async_result,
        )
        self.status_display.configure(
            text="Dialog opened asynchronously (main app did not pause)",
            text_color=("gray40", "gray60"),
        )

    def _test_delayed_popup(self) -> None:
        """Launch a popup after a 5-second countdown to verify centering when minimized."""
        def _tick(remaining: int) -> None:
            if remaining > 0:
                self.status_display.configure(
                    text=f"Launching popup in {remaining}s... Minimize this window now!",
                    text_color=("#D97706", "#FBBF24"),
                )
                self.after(1000, _tick, remaining - 1)
            else:
                self.status_display.configure(
                    text="Popup launched!",
                    text_color=("gray40", "gray60"),
                )
                popup = CTkPopup(
                    master=self,
                    title="Screen Centered Test",
                    message=(
                        "If you minimized the main window, this popup detected that master was "
                        "not viewable and centered directly on your primary monitor!"
                    ),
                    preset="info",
                )
                self._log(popup.get())

        _tick(DELAY_TIME_SECONDS)

    def _on_closing(self) -> None:
        """Gracefully terminate mainloop and destroy window.

        Calling quit() breaks out of Tkinter's C event loop immediately so
        Python does not hang waiting inside mainloop() after window close.
        """
        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = DemoApp()
    enable_debug_mode(app)  # Enables debug mode if the module is imported
    app.mainloop()
