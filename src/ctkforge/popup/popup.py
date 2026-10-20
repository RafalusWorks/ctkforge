"""Main CTkPopup dialog implementation.

A modern, robust, and DPI-aware replacement for CTkMessagebox featuring:
  - Strict CustomTkinter API parity: .cget() and .configure() methods
  - Primary text parameter aligned with CTk standard ('text')
  - Zero arbitrary property setters or getters for options
  - 4 semantic button roles with dedicated resting and hover colors
  - Decoupled semantic return values (booleans, tokens)
  - Hidden-staging window lifecycle preventing geometry jumps
  - The Courier Rule: safe return values without widget destruction errors
  - Automatic switching between CTkLabel and copyable CTkTextbox for long logs
  - Option B Smart Fail-Safe icon resolution
"""

import tkinter as tk
from collections.abc import Callable
from contextlib import suppress
from typing import Any, override

import customtkinter as ctk

from ctkforge.debug import DEBUG_BANNER, is_debug_mode, print_window_telemetry
from ctkforge.geometry import scale, unscale

from .buttons import create_button, normalize_buttons
from .constants import (
    DEFAULT_POPUP_WIDTH,
    DEFAULT_WRAPLENGTH,
    ICON_DISPLAY_SIZE,
    MAX_LABEL_HEIGHT,
    MESSAGE_FONT_SIZE,
    POPUP_BORDER_COLOR,
    POPUP_BORDER_WIDTH,
    PRESETS,
    ROLE_COLORS,
    TEXTBOX_HEIGHT,
    TEXTBOX_WIDTH_PADDING,
)
from .icons import resolve_icon

_SENTINEL = object()


class CTkPopup(ctk.CTkToplevel):
    """Modern, customizable dialog and message box for CustomTkinter.

    Adheres strictly to standard CustomTkinter widget design principles:
    all options are configured via .configure() and read via .cget(),
    with zero public property setters for widget configuration.
    """

    PRESETS = PRESETS
    ROLE_COLORS = ROLE_COLORS

    def __init__(
        self,
        master: Any = None,
        title: str | None = None,
        text: str = "",
        icon: Any = None,
        buttons: Any = None,
        preset: str | None = None,
        default_button: Any = _SENTINEL,
        cancel_button: Any = _SENTINEL,
        callback: Callable[[Any], None] | None = None,
        sound: bool = False,
        wraplength: int = DEFAULT_WRAPLENGTH,
        max_label_height: int = MAX_LABEL_HEIGHT,
        width: int = DEFAULT_POPUP_WIDTH,
        height: int | None = None,
        corner_radius: int = 12,
        border_width: int = POPUP_BORDER_WIDTH,
        border_color: str | tuple[str, str] = POPUP_BORDER_COLOR,
        fg_color: str | tuple[str, str] | None = None,
        text_color: str | tuple[str, str] | None = None,
        font: ctk.CTkFont | tuple[Any, ...] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize and display the CTkPopup dialog.

        Args:
            master: Parent window or frame.
            title: OS window title text.
            text: Primary message or prompt to display.
            icon: Image object, file path, stock preset name, or None.
            buttons: List of button strings, tuples, or dicts.
            preset: Preset template name ('info', 'warning', 'error', 'question', 'success').
            default_button: Value returned when pressing <Return>.
            cancel_button: Value returned when pressing <Escape> or clicking 'X'.
            callback: Optional non-blocking callback function (callback(result)).
            sound: If True, plays system bell upon appearing.
            wraplength: Maximum horizontal wrap width for short messages in logical pixels.
            max_label_height: Threshold in logical pixels before switching to CTkTextbox.
            width: Target dialog window width in logical pixels.
            height: Optional explicit dialog window height in logical pixels.
            corner_radius: Corner curvature of the popup frame.
            border_width: Outline border thickness of the popup frame.
            border_color: Outline border color of the popup frame.
            fg_color: Frame background color or theme tuple.
            text_color: Message text color or theme tuple.
            font: Optional CustomTkinter font or font tuple for the message text.
            **kwargs: Additional parameters forwarded to CTkToplevel or 'message' alias.
        """
        # Alias: accept 'message' as an alternate parameter name for 'text'
        if "message" in kwargs:
            passed_message = str(kwargs.pop("message"))
            if not text:
                text = passed_message

        super().__init__(master, **kwargs)

        # 1. Staging Protocol: Immediately withdraw window to prevent geometry jump
        self.withdraw()

        self._callback = callback
        self._result: Any = None
        self._finished: bool = False
        self._sound = sound
        self._wraplength = wraplength
        self._max_label_height = max_label_height
        self._width = width
        self._height = height
        self._corner_radius = corner_radius
        self._border_width = border_width
        self._border_color = border_color
        self._fg_color = fg_color
        self._text_color = text_color
        self._font = font
        self._text = text
        self._icon_input = icon
        self._preset = preset
        self._raw_buttons = buttons

        # Determine effective preset
        preset_key = preset
        if preset_key is None and isinstance(icon, str) and icon in self.PRESETS:
            preset_key = icon
        self._preset_key = preset_key

        preset_config = self.PRESETS.get(preset_key, {}) if preset_key else {}

        # Resolve window title
        if title is not None:
            self._title_text = title
        elif preset_config.get("title"):
            self._title_text = str(preset_config["title"])
        else:
            self._title_text = "Alert"

        if is_debug_mode() and DEBUG_BANNER not in self._title_text:
            self._title_text = f"{self._title_text}{DEBUG_BANNER}"

        self.title(self._title_text)
        self.resizable(False, False)

        # Ensure window is transient relative to master if master exists
        if self.master is not None and isinstance(
            self.master, (ctk.CTk, ctk.CTkToplevel)
        ):
            with suppress(tk.TclError):
                self.transient(self.master)

        # Resolve buttons input
        raw_buttons = buttons if buttons is not None else preset_config.get("buttons")
        self._normalized_buttons = normalize_buttons(raw_buttons)

        # Resolve default_button (<Return> action)
        if default_button is not _SENTINEL:
            self._default_value = default_button
        elif "default_button" in preset_config:
            self._default_value = preset_config["default_button"]
        else:
            primary_btn = next(
                (b for b in self._normalized_buttons if b.get("role") == "primary"),
                None,
            )
            self._default_value = (
                primary_btn["value"]
                if primary_btn
                else self._normalized_buttons[0]["value"]
            )

        # Resolve cancel_button (<Escape> and 'X' action)
        if cancel_button is not _SENTINEL:
            self._cancel_value = cancel_button
        elif "cancel_button" in preset_config:
            self._cancel_value = preset_config["cancel_button"]
        else:
            cancel_btn = next(
                (b for b in self._normalized_buttons if b.get("role") == "cancel"), None
            )
            if cancel_btn:
                self._cancel_value = cancel_btn["value"]
            elif len(self._normalized_buttons) == 1:
                self._cancel_value = self._normalized_buttons[0]["value"]
            else:
                self._cancel_value = None

        # Resolve icon (Option B Smart Fail-Safe)
        icon_source = icon if icon is not None else preset_config.get("icon")
        self._icon_image = resolve_icon(
            icon_source, preset_name=preset_key, display_size=ICON_DISPLAY_SIZE
        )

        # Child widget references for dynamic .configure() updates
        self._icon_label: ctk.CTkLabel | None = None
        self._message_label: ctk.CTkLabel | None = None
        self._message_textbox: ctk.CTkTextbox | None = None
        self._action_buttons: list[ctk.CTkButton] = []

        # 2. Build the visual interface
        self._build_ui()

        # 3. Bind Keyboard and Window Close Protocols
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.bind("<Return>", lambda _e: self._on_default())
        if is_debug_mode():
            self.bind("<F12>", self._print_debug_telemetry)

        # 4. Measure and Center over Master (or Screen)
        self._center_and_reveal(reposition=True)

        # 5. Optional audio alert
        if self._sound:
            with suppress(tk.TclError):
                self.bell()

        # 6. If non-blocking callback is provided, set modal grab without waiting
        if self._callback is not None:
            self.grab_set()

    def _build_ui(self) -> None:
        """Construct the popup layout widgets."""
        # Outermost container frame
        self._main_frame = ctk.CTkFrame(
            self,
            corner_radius=self._corner_radius,
            border_width=self._border_width,
            border_color=self._border_color,
            fg_color=self._fg_color,
        )
        self._main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Content area (Icon + Message)
        self._content_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, padx=20, pady=(20, 16))

        # Icon widget (if available)
        self._update_icon()

        # Text area: dynamically chooses CTkLabel or CTkTextbox
        self._update_text()

        # Button row container
        self._button_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        self._button_frame.pack(fill="x", padx=20, pady=(0, 18))

        self._button_container = ctk.CTkFrame(self._button_frame, fg_color="transparent")
        self._button_container.pack(anchor="e")

        self._render_buttons()

    def _render_buttons(self) -> None:
        """Render all normalized action buttons inside the button container."""
        for btn in self._action_buttons:
            with suppress(tk.TclError):
                btn.destroy()
        self._action_buttons.clear()

        for btn_spec in self._normalized_buttons:
            btn = create_button(
                self._button_container,
                btn_spec,
                on_click=self._on_button_click,
                role_colors=self.ROLE_COLORS,
            )
            btn.pack(side="left", padx=5)
            self._action_buttons.append(btn)

    def _update_icon(self) -> None:
        """Synchronize the icon widget with current _icon_image."""
        if self._icon_image is not None:
            if self._icon_label is None:
                self._icon_label = ctk.CTkLabel(
                    self._content_frame,
                    text="",
                    image=self._icon_image,
                )
                self._icon_label.pack(side="left", anchor="n", padx=(0, 18), pady=(4, 0))
            else:
                self._icon_label.configure(image=self._icon_image)
        elif self._icon_label is not None:
            self._icon_label.destroy()
            self._icon_label = None

    def _measure_text_height(
        self, text: str, wraplength: int, font: ctk.CTkFont | tuple[Any, ...] | None
    ) -> int:
        """Measure natural rendered height of wrapped text in logical (96 DPI baseline) pixels."""
        probe = ctk.CTkLabel(
            self,
            text=text,
            wraplength=wraplength,
            justify="left",
            font=font,
        )
        probe.update_idletasks()
        measured_height = unscale(self, probe.winfo_reqheight())
        probe.destroy()
        return measured_height

    def _update_text(self) -> None:
        """Dynamically render or update message inside a CTkLabel or CTkTextbox."""
        message_font = (
            self._font if self._font is not None else ctk.CTkFont(size=MESSAGE_FONT_SIZE)
        )
        text_height = self._measure_text_height(self._text, self._wraplength, message_font)

        if text_height <= self._max_label_height:
            # Clean up textbox if previously long text
            if self._message_textbox is not None:
                self._message_textbox.destroy()
                self._message_textbox = None

            if self._message_label is None:
                self._message_label = ctk.CTkLabel(
                    self._content_frame,
                    text=self._text,
                    wraplength=self._wraplength,
                    justify="left",
                    font=message_font,
                    text_color=self._text_color,
                )
                self._message_label.pack(side="left", fill="both", expand=True, anchor="w")
            else:
                config_kwargs: dict[str, Any] = {
                    "text": self._text,
                    "wraplength": self._wraplength,
                    "font": message_font,
                }
                if self._text_color is not None:
                    config_kwargs["text_color"] = self._text_color
                self._message_label.configure(**config_kwargs)
        else:
            # Long text (e.g. exception tracebacks): switch to read-only CTkTextbox
            if self._message_label is not None:
                self._message_label.destroy()
                self._message_label = None

            textbox_font = (
                self._font
                if (self._font is not None and "Traceback" not in self._text)
                else ctk.CTkFont(
                    family="Consolas" if "Traceback" in self._text else "Segoe UI", size=12
                )
            )

            if self._message_textbox is None:
                self._message_textbox = ctk.CTkTextbox(
                    self._content_frame,
                    width=self._wraplength + TEXTBOX_WIDTH_PADDING,
                    height=TEXTBOX_HEIGHT,
                    activate_scrollbars=True,
                    font=textbox_font,
                    text_color=self._text_color,
                )
                self._message_textbox.pack(side="left", fill="both", expand=True)
            else:
                self._message_textbox.configure(
                    state="normal",
                    width=self._wraplength + TEXTBOX_WIDTH_PADDING,
                    font=textbox_font,
                )
                if self._text_color is not None:
                    self._message_textbox.configure(text_color=self._text_color)

            self._message_textbox.delete("1.0", "end")
            self._message_textbox.insert("1.0", self._text)
            self._message_textbox.configure(state="disabled")

    def _calculate_coordinates(
        self, phys_width: int, phys_height: int
    ) -> tuple[int, int]:
        """Calculate physical (x, y) screen coordinates centered over master or monitor."""
        master = self.master
        master_is_visible = False

        if master is not None:
            with suppress(tk.TclError, AttributeError):
                if (
                    master.state() not in ("iconic", "withdrawn")
                    and master.winfo_viewable()
                ):
                    master_is_visible = True

        if master_is_visible:
            target_x = master.winfo_rootx() + (master.winfo_width() - phys_width) // 2
            target_y = master.winfo_rooty() + (master.winfo_height() - phys_height) // 2
        else:
            phys_screen_w, phys_screen_h = scale(
                self, self.winfo_screenwidth(), self.winfo_screenheight()
            )
            target_x = (phys_screen_w - phys_width) // 2
            target_y = (phys_screen_h - phys_height) // 2

        return max(0, target_x), max(0, target_y)

    def _center_and_reveal(self, reposition: bool = True) -> None:
        """Calculate DPI-aware coordinates and reveal window without geometry jump."""
        self.update_idletasks()

        base_req_w, base_req_h = unscale(
            self, self.winfo_reqwidth(), self.winfo_reqheight()
        )
        final_base_w = max(base_req_w, self._width)
        final_base_h = self._height if self._height is not None else base_req_h

        final_phys_w, final_phys_h = scale(self, final_base_w, final_base_h)

        if reposition:
            target_x, target_y = self._calculate_coordinates(final_phys_w, final_phys_h)
            self.geometry(f"{final_base_w}x{final_base_h}+{target_x}+{target_y}")
            self.deiconify()
            self.lift()
            self.focus_force()
        else:
            # Preserve current top-left position while updating dimensions
            cur_x = self.winfo_x()
            cur_y = self.winfo_y()
            self.geometry(f"{final_base_w}x{final_base_h}+{cur_x}+{cur_y}")

    @override
    def cget(self, attribute_name: str) -> Any:
        """Retrieve popup widget configuration option.

        Args:
            attribute_name: Name of the property ('text', 'title', 'icon', etc.).

        Returns:
            The configured value.
        """
        match attribute_name:
            case "text" | "message":
                return self._text
            case "title":
                return self._title_text
            case "icon":
                return self._icon_input
            case "preset":
                return self._preset
            case "buttons":
                return self._raw_buttons
            case "width":
                return self._width
            case "height":
                return self._height
            case "corner_radius":
                return self._corner_radius
            case "border_width":
                return self._border_width
            case "border_color":
                return self._border_color
            case "fg_color":
                return self._fg_color
            case "text_color":
                return self._text_color
            case "font":
                return self._font
            case "sound":
                return self._sound
            case "wraplength":
                return self._wraplength
            case "max_label_height":
                return self._max_label_height
            case "default_button":
                return self._default_value
            case "cancel_button":
                return self._cancel_value
            case "callback":
                return self._callback
            case "result":
                return self._result
            case _:
                return super().cget(attribute_name)

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Update popup configuration options and refresh child widgets.

        Args:
            require_redraw: Passed to superclass configure if needed.
            **kwargs: Configuration options to update ('text', 'title', 'icon', etc.).
        """
        needs_regeometry = False

        if "title" in kwargs:
            self._title_text = str(kwargs.pop("title"))
            if is_debug_mode() and DEBUG_BANNER not in self._title_text:
                self._title_text = f"{self._title_text}{DEBUG_BANNER}"
            self.title(self._title_text)

        if "text" in kwargs or "message" in kwargs:
            raw_text = kwargs.pop("text") if "text" in kwargs else kwargs.pop("message")
            self._text = str(raw_text)
            self._update_text()
            needs_regeometry = True

        if "icon" in kwargs:
            self._icon_input = kwargs.pop("icon")
            self._icon_image = resolve_icon(
                self._icon_input,
                preset_name=self._preset_key,
                display_size=ICON_DISPLAY_SIZE,
            )
            self._update_icon()
            needs_regeometry = True

        if "wraplength" in kwargs:
            self._wraplength = int(kwargs.pop("wraplength"))
            self._update_text()
            needs_regeometry = True

        if "max_label_height" in kwargs:
            self._max_label_height = int(kwargs.pop("max_label_height"))
            self._update_text()
            needs_regeometry = True

        if "width" in kwargs:
            self._width = int(kwargs.pop("width"))
            needs_regeometry = True

        if "height" in kwargs:
            val = kwargs.pop("height")
            self._height = int(val) if val is not None else None
            needs_regeometry = True

        if "corner_radius" in kwargs:
            self._corner_radius = int(kwargs.pop("corner_radius"))
            self._main_frame.configure(corner_radius=self._corner_radius)

        if "border_width" in kwargs:
            self._border_width = int(kwargs.pop("border_width"))
            self._main_frame.configure(border_width=self._border_width)

        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            self._main_frame.configure(border_color=self._border_color)

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            self._main_frame.configure(fg_color=self._fg_color)

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            if self._message_label is not None:
                self._message_label.configure(text_color=self._text_color)
            elif self._message_textbox is not None:
                self._message_textbox.configure(text_color=self._text_color)

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            self._update_text()
            needs_regeometry = True

        if "sound" in kwargs:
            self._sound = bool(kwargs.pop("sound"))

        if "callback" in kwargs:
            self._callback = kwargs.pop("callback")

        if "buttons" in kwargs:
            self._raw_buttons = kwargs.pop("buttons")
            self._normalized_buttons = normalize_buttons(self._raw_buttons)
            self._render_buttons()
            needs_regeometry = True

        if "default_button" in kwargs:
            self._default_value = kwargs.pop("default_button")

        if "cancel_button" in kwargs:
            self._cancel_value = kwargs.pop("cancel_button")

        if "preset" in kwargs:
            preset_name = kwargs.pop("preset")
            if preset_name in self.PRESETS:
                self._preset = preset_name
                self._preset_key = preset_name
                p_cfg = self.PRESETS[preset_name]
                if "title" not in kwargs and p_cfg.get("title"):
                    self._title_text = str(p_cfg["title"])
                    if is_debug_mode() and DEBUG_BANNER not in self._title_text:
                        self._title_text = f"{self._title_text}{DEBUG_BANNER}"
                    self.title(self._title_text)
                if "icon" not in kwargs and p_cfg.get("icon"):
                    self._icon_input = p_cfg["icon"]
                    self._icon_image = resolve_icon(
                        self._icon_input,
                        preset_name=self._preset_key,
                        display_size=ICON_DISPLAY_SIZE,
                    )
                    self._update_icon()
                if "buttons" not in kwargs and p_cfg.get("buttons"):
                    self._raw_buttons = p_cfg["buttons"]
                    self._normalized_buttons = normalize_buttons(self._raw_buttons)
                    self._render_buttons()
                if "default_button" not in kwargs and "default_button" in p_cfg:
                    self._default_value = p_cfg["default_button"]
                if "cancel_button" not in kwargs and "cancel_button" in p_cfg:
                    self._cancel_value = p_cfg["cancel_button"]
                needs_regeometry = True

        if kwargs:
            super().configure(require_redraw=require_redraw, **kwargs)

        if needs_regeometry and not self._finished and self.winfo_exists():
            self._center_and_reveal(reposition=False)

    def _on_button_click(self, value: Any) -> None:
        """Handle user clicking a button widget."""
        self._finish(value)

    def _on_default(self) -> None:
        """Handle <Return> key: triggers designated default action."""
        self._finish(self._default_value)

    def _on_cancel(self) -> None:
        """Handle <Escape> or window 'X' button: triggers safe cancel/dismiss action."""
        self._finish(self._cancel_value)

    def _finish(self, chosen_value: Any) -> None:
        """The Courier Rule: save return value, release grab, and destroy cleanly."""
        if self._finished:
            return
        self._finished = True
        self._result = chosen_value

        with suppress(tk.TclError):
            self.grab_release()

        with suppress(tk.TclError):
            self.destroy()

        if self._callback is not None:
            self._callback(self._result)

    def get(self) -> Any:
        """Synchronously wait for the user to make a choice and return the value."""
        if not self._finished and self.winfo_exists():
            with suppress(tk.TclError):
                self.grab_set()
                self.wait_window(self)
        return self._result

    def _print_debug_telemetry(self, event: Any = None) -> None:
        """Print window size, scaling, and baseline dimensions to terminal when F12 is pressed."""
        print_window_telemetry(self)
