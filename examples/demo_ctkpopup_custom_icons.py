"""Demonstration of Custom Icons in CTkPopup.

This demo shows developers how to use custom icons in their own applications:
  Baseline:  Stock Preset      (built-in icons like preset="warning")
  Option 1:  Relative Path     (e.g. icon="images/custom_star.png")
  Option 2:  Custom CTkImage   (for distinct Light Mode & Dark Mode images)
"""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image

# CTkPopup handles all path finding and PyInstaller bundling automatically.
from ctkforge import CTkPopup, resource_path


class CustomIconDemo(ctk.CTk):
    """Developer showcase window demonstrating how to supply custom icons to CTkPopup."""

    def __init__(self) -> None:
        super().__init__()

        self.title("CTkPopup - Custom Icon Demo")
        self.geometry("520x400")
        self.minsize(480, 360)

        # Set up standard CustomTkinter appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Graceful close protocol: quit() breaks Tcl event loop so Python doesn't hang in mainloop
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._build_ui()

    def _build_ui(self) -> None:
        """Create the window header and the demonstration buttons."""
        # Top title section with theme switch
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))
        header_frame.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(
            title_box,
            text="Custom Icons in CTkPopup",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Compare built-in stock icons with custom icon approaches",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Theme toggle switch in top-right corner
        self.theme_switch = ctk.CTkSwitch(
            header_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="Dark",
            offvalue="Light",
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=0, column=1, sticky="e")

        # Main button container
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Baseline: Standard Built-in Warning (No custom icon)
        btn_stock = ctk.CTkButton(
            content_frame,
            text='Standard Warning  ( Built-in preset="warning" )',
            command=self._show_stock_warning_popup,
            height=40,
            fg_color="#D97706",
            hover_color="#B45309",
        )
        btn_stock.pack(fill="x", padx=20, pady=(16, 8))

        # Button 1: Relative Path
        btn_relative = ctk.CTkButton(
            content_frame,
            text='1. Relative Path  ( "images/custom_star.png" )',
            command=self._show_relative_path_popup,
            height=40,
        )
        btn_relative.pack(fill="x", padx=20, pady=8)

        # Button 2: Pre-configured CTkImage
        btn_ctk_image = ctk.CTkButton(
            content_frame,
            text="2. Pre-configured CTkImage  ( Light & Dark Mode )",
            command=self._show_ctk_image_popup,
            height=40,
        )
        btn_ctk_image.pack(fill="x", padx=20, pady=8)

        # Status feedback label at the bottom
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="Click any button above to test.",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray60",
        )
        self.status_label.pack(side="bottom", pady=14)

    def _toggle_theme(self) -> None:
        """Switch appearance mode between Dark and Light."""
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    # -------------------------------------------------------------------------
    # Baseline: Standard Built-in Warning
    # -------------------------------------------------------------------------
    def _show_stock_warning_popup(self) -> None:
        popup = CTkPopup(
            master=self,
            title="System Alert",
            message=(
                "Warning: Low coffee levels detected.\n\n"
                "Your coding efficiency may drop below acceptable thresholds."
            ),
            preset="warning",
            buttons=["Refill Cup", "Ignore Risk"],
        )
        result = popup.get()
        self.status_label.configure(text=f"Stock warning result: {result}")

    # -------------------------------------------------------------------------
    # 1. Relative Path
    # -------------------------------------------------------------------------
    def _show_relative_path_popup(self) -> None:
        popup = CTkPopup(
            master=self,
            title="Destruction Protocol",
            message=(
                "This popup has a custom icon!\n\n"
                "Do you want to erase your operating system and start a new life in the woods?"
            ),
            icon="images/custom_star.png",
            buttons=[{"text": "Erase Everything", "role": "destructive"}, "Cancel"],
        )
        result = popup.get()
        self.status_label.configure(text=f"Relative path result: {result}")

    # -------------------------------------------------------------------------
    # 2. Pre-configured ctk.CTkImage
    # -------------------------------------------------------------------------
    def _show_ctk_image_popup(self) -> None:
        light_path = resource_path("images/custom_star_light.png")
        dark_path = resource_path("images/custom_star.png")

        with Image.open(light_path) as light_img, Image.open(dark_path) as dark_img:
            custom_icon = ctk.CTkImage(
                light_image=light_img.copy(),
                dark_image=dark_img.copy(),
                size=(48, 48),
            )

        popup = CTkPopup(
            master=self,
            title="Self-Destruct Sequence",
            message=(
                "Self-destruct sequence initiated!\n\n"
                "This popup uses a dual-theme CTkImage icon (adapts to Light & Dark mode)."
            ),
            icon=custom_icon,
            buttons=["Abort Mission", "Deploy Parachute"],
        )
        result = popup.get()
        self.status_label.configure(text=f"CTkImage result: {result}")

    def _on_closing(self) -> None:
        """Gracefully terminate mainloop and destroy window.

        Calling quit() breaks out of Tkinter's C event loop immediately so
        Python does not hang waiting inside mainloop() after window close.
        """
        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = CustomIconDemo()
    app.mainloop()
