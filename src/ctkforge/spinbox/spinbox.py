"""Spinbox widget for CustomTkinter.

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
"""

from collections.abc import Callable
from typing import Any, override

import customtkinter as ctk

__all__ = ["CTkSpinbox"]


class CTkSpinbox(ctk.CTkFrame):
    """Spinbox widget modeled after the classic vertical-arrow layout.

    Provides a numeric entry field paired with stacked up/down micro-buttons,
    matching CustomTkinter geometry mechanics, corner radius, and theme tokens.
    """

    def __init__(
        self,
        master: Any,
        width: int = 70,
        height: int = 28,
        start_value: int = 0,
        min_value: int = 0,
        max_value: int = 100,
        step: int = 5,
        corner_radius: int | None = None,
        border_width: int | None = None,
        fg_color: str | tuple[str, str] | None = None,
        border_color: str | tuple[str, str] | None = None,
        font: tuple[str, int] | ctk.CTkFont | None = None,
        text_color: str | tuple[str, str] | None = None,
        button_color: str | tuple[str, str] | None = None,
        button_hover_color: str | tuple[str, str] | None = None,
        state: str = "normal",
        justify: str = "center",
        command: Callable[[int], None] | None = None,
        **kwargs: Any,
    ) -> None:
        theme = ctk.ThemeManager.theme
        resolved_corner_radius = (
            theme["CTkEntry"]["corner_radius"]
            if corner_radius is None
            else corner_radius
        )
        resolved_border_width = (
            theme["CTkEntry"]["border_width"] if border_width is None else border_width
        )
        resolved_fg_color = (
            theme["CTkEntry"]["fg_color"] if fg_color is None else fg_color
        )
        resolved_border_color = (
            theme["CTkEntry"]["border_color"] if border_color is None else border_color
        )

        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=resolved_corner_radius,
            border_width=resolved_border_width,
            fg_color=resolved_fg_color,
            border_color=resolved_border_color,
            **kwargs,
        )

        self._min_value = min_value
        self._max_value = max_value
        self._step = max(1, step)
        self._state = state
        self._justify = justify
        self.command = command
        self._value = max(min_value, min(max_value, start_value))

        # Typography and colors
        self._font = font if font is not None else ctk.CTkFont(size=13)
        self._text_color = (
            theme["CTkEntry"]["text_color"] if text_color is None else text_color
        )
        self._button_color = (
            theme["CTkButton"]["fg_color"] if button_color is None else button_color
        )
        self._button_hover_color = (
            theme["CTkButton"]["hover_color"]
            if button_hover_color is None
            else button_hover_color
        )

        # Enforce exact bounding dimensions like CTkComboBox
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

        # Center numeric entry field
        self._entry = ctk.CTkEntry(
            self,
            width=1,
            border_width=0,
            fg_color="transparent",
            justify=self._justify,
            font=self._font,
            text_color=self._text_color,
        )
        self._entry.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(6, 2), pady=2)
        self._entry.insert(0, str(self._value))

        # Event bindings for text and arrow keys
        self._entry.bind("<FocusOut>", lambda _: self._on_entry_changed())
        self._entry.bind("<Return>", lambda _: self._on_entry_changed())
        self._entry.bind("<Up>", lambda _: (self._increment(), "break")[1])
        self._entry.bind("<Down>", lambda _: (self._decrement(), "break")[1])
        self.bind("<MouseWheel>", self._on_mousewheel)
        self._entry.bind("<MouseWheel>", self._on_mousewheel)

        # Micro-buttons setup
        btn_w, btn_h, btn_font = self._calculate_button_geometry(height)

        self._up_button = ctk.CTkButton(
            self,
            text="▲",
            width=btn_w,
            height=btn_h,
            font=btn_font,
            corner_radius=2,
            fg_color=self._button_color,
            hover_color=self._button_hover_color,
            command=self._increment,
        )
        self._up_button.grid(row=0, column=1, sticky="nsew", padx=(0, 3), pady=(2, 1))

        self._down_button = ctk.CTkButton(
            self,
            text="▼",
            width=btn_w,
            height=btn_h,
            font=btn_font,
            corner_radius=2,
            fg_color=self._button_color,
            hover_color=self._button_hover_color,
            command=self._decrement,
        )
        self._down_button.grid(row=1, column=1, sticky="nsew", padx=(0, 3), pady=(1, 2))

        if self._state == "disabled":
            self._apply_state("disabled")

    @property
    def entry(self) -> ctk.CTkEntry:
        """Direct access to the internal text box for focus or inspection."""
        return self._entry

    @property
    def min_value(self) -> int:
        """Lowest number allowed in the spinbox."""
        return self._min_value

    @property
    def max_value(self) -> int:
        """Highest number allowed in the spinbox."""
        return self._max_value

    @property
    def step(self) -> int:
        """Amount added or subtracted on each tick."""
        return self._step

    def focus(self) -> None:
        """Move keyboard focus into the text box."""
        self._entry.focus()

    def focus_set(self) -> None:
        """Legacy Tkinter alias to move keyboard focus into the text box."""
        self._entry.focus_set()

    def _calculate_button_geometry(self, height: int) -> tuple[int, int, ctk.CTkFont]:
        """Calculate the width, height, and font size for the up and down arrow buttons."""
        btn_h = max(8, int((height - 6) / 2))
        btn_w = max(18, min(24, int(height * 0.75)))
        f_size = max(6, min(9, int(height / 4)))
        return btn_w, btn_h, ctk.CTkFont(size=f_size, weight="bold")

    def _update_button_proportions(self, height: int) -> None:
        """Resize the arrow buttons to fit neatly when the widget height changes."""
        btn_w, btn_h, btn_font = self._calculate_button_geometry(height)
        self._up_button.configure(width=btn_w, height=btn_h, font=btn_font)
        self._down_button.configure(width=btn_w, height=btn_h, font=btn_font)

    def _apply_state(self, new_state: str) -> None:
        """Enable or disable the text box and arrow buttons."""
        self._state = new_state
        self._entry.configure(state=self._state)
        self._up_button.configure(state=self._state)
        self._down_button.configure(state=self._state)

    def _increment(self) -> None:
        """Increase the value by one step."""
        if self._state == "disabled":
            return
        self.set(self._value + self._step)

    def _decrement(self) -> None:
        """Decrease the value by one step."""
        if self._state == "disabled":
            return
        self.set(self._value - self._step)

    def _on_entry_changed(self) -> None:
        """Read typed text, check if it is a valid number, and update the value."""
        if self._state == "disabled":
            return
        raw_text = self._entry.get().strip()
        try:
            val = int(raw_text)
            self.set(val)
        except ValueError:
            self.set(self._value)

    def _on_mousewheel(self, event: Any) -> None:
        """Increase or decrease the number when turning the mouse wheel."""
        if self._state == "disabled":
            return
        if event.delta > 0:
            self._increment()
        elif event.delta < 0:
            self._decrement()

    def get(self) -> int:
        """Return the current number."""
        return self._value

    def set(self, value: int) -> None:
        """Set the number, keeping it within the minimum and maximum limits."""
        self._value = max(self._min_value, min(self._max_value, value))
        current_state = self._entry.cget("state")
        if current_state != "normal":
            self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.insert(0, str(self._value))
        if current_state != "normal":
            self._entry.configure(state=current_state)
        if self.command:
            self.command(self._value)

    @override
    def cget(self, attribute_name: str) -> Any:
        """Read a configuration option from the spinbox."""
        match attribute_name:
            case "min_value":
                return self._min_value
            case "max_value":
                return self._max_value
            case "step":
                return self._step
            case "command":
                return self.command
            case "state":
                return self._state
            case "justify":
                return self._justify
            case "font":
                return self._font
            case "text_color":
                return self._text_color
            case "button_color":
                return self._button_color
            case "button_hover_color":
                return self._button_hover_color
            case _:
                return super().cget(attribute_name)

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Update spinbox settings and refresh child widgets."""
        if "min_value" in kwargs:
            self._min_value = int(kwargs.pop("min_value"))
            self.set(self._value)

        if "max_value" in kwargs:
            self._max_value = int(kwargs.pop("max_value"))
            self.set(self._value)

        if "step" in kwargs:
            self._step = max(1, int(kwargs.pop("step")))

        if "command" in kwargs:
            self.command = kwargs.pop("command")

        if "state" in kwargs:
            self._apply_state(str(kwargs.pop("state")))

        if "justify" in kwargs:
            self._justify = str(kwargs.pop("justify"))
            self._entry.configure(justify=self._justify)

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            self._entry.configure(font=self._font)

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            self._entry.configure(text_color=self._text_color)

        if "button_color" in kwargs:
            self._button_color = kwargs.pop("button_color")
            self._up_button.configure(fg_color=self._button_color)
            self._down_button.configure(fg_color=self._button_color)

        if "button_hover_color" in kwargs:
            self._button_hover_color = kwargs.pop("button_hover_color")
            self._up_button.configure(hover_color=self._button_hover_color)
            self._down_button.configure(hover_color=self._button_hover_color)

        if "height" in kwargs:
            self._update_button_proportions(int(kwargs["height"]))

        super().configure(require_redraw=require_redraw, **kwargs)
