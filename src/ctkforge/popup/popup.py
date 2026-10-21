"""Main CTkPopup popup dialog.

Shows an interactive modal dialog with:
  - Standard widget configuration via .cget() and .configure()
  - Primary 'text' parameter matching CustomTkinter conventions
  - Semantic button roles with automatic hover styling
  - DPI-aware geometry positioning without screen jumps
  - Automatic switching to scrollable text boxes for long text

Author: Rafalus
Repository: https://github.com/RafalusWorks/ctkforge
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
    BUTTON_CONTAINER_PADDING_BOTTOM,
    BUTTON_CONTAINER_PADDING_X,
    BUTTON_SPACING,
    CONTENT_PADDING_X,
    CONTENT_PADDING_Y,
    DEFAULT_CORNER_RADIUS,
    DEFAULT_POPUP_WIDTH,
    DEFAULT_WRAPLENGTH,
    ICON_DISPLAY_SIZE,
    ICON_PADDING_RIGHT,
    ICON_PADDING_TOP,
    MAX_LABEL_HEIGHT,
    MESSAGE_FONT_SIZE,
    POPUP_BORDER_COLOR,
    POPUP_BORDER_WIDTH,
    POPUP_PADDING,
    PRESETS,
    ROLE_COLORS,
    TEXTBOX_FONT_SIZE,
    TEXTBOX_HEIGHT,
    TEXTBOX_WIDTH_PADDING,
)
from .icons import resolve_icon

_SENTINEL = object()


def _format_window_title(raw_title: str) -> str:
    """Format the window title, appending the debug banner if in debug mode."""
    if is_debug_mode() and DEBUG_BANNER not in raw_title:
        return f"{raw_title}{DEBUG_BANNER}"
    return raw_title


class CTkPopup(ctk.CTkToplevel):
    """Modern modal dialog and message box for CustomTkinter.

    Follows standard CustomTkinter widget design principles where all
    options are configured via .configure() and queried via .cget().
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
        corner_radius: int = DEFAULT_CORNER_RADIUS,
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

        # 1. Immediately withdraw window to prevent geometry jump
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

        # Child widget references for dynamic configuration
        self._icon_label: ctk.CTkLabel | None = None
        self._message_label: ctk.CTkLabel | None = None
        self._message_textbox: ctk.CTkTextbox | None = None
        self._action_buttons: list[ctk.CTkButton] = []

        # 2. Resolve preset defaults, titles, buttons, and icon
        self._resolve_initial_state(
            title=title,
            icon=icon,
            buttons=buttons,
            preset=preset,
            default_button=default_button,
            cancel_button=cancel_button,
        )

        # 3. Setup window protocols and bindings
        self._setup_window()

        # 4. Build visual interface and present dialog
        self._build_ui()
        self._center_and_reveal(reposition=True)

        if self._sound:
            with suppress(tk.TclError):
                self.bell()

        if self._callback is not None:
            self.grab_set()

    def _resolve_initial_state(
        self,
        title: str | None,
        icon: Any,
        buttons: Any,
        preset: str | None,
        default_button: Any,
        cancel_button: Any,
    ) -> None:
        """Resolve preset defaults, title text, button actions, and icons."""
        preset_key = preset
        if preset_key is None and isinstance(icon, str) and icon in self.PRESETS:
            preset_key = icon
        self._preset_key = preset_key

        preset_config = self.PRESETS.get(preset_key, {}) if preset_key else {}

        # Resolve title
        if title is not None:
            resolved_title = title
        elif preset_config.get("title"):
            resolved_title = str(preset_config["title"])
        else:
            resolved_title = "Alert"
        self._title_text = _format_window_title(resolved_title)

        # Resolve buttons
        raw_buttons = buttons if buttons is not None else preset_config.get("buttons")
        self._normalized_buttons = normalize_buttons(raw_buttons)

        # Resolve default (<Return>) button
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

        # Resolve cancel (<Escape> and 'X') button
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

        # Resolve icon
        icon_source = icon if icon is not None else preset_config.get("icon")
        self._icon_image = resolve_icon(
            icon_source, preset_name=preset_key, display_size=ICON_DISPLAY_SIZE
        )

    def _setup_window(self) -> None:
        """Configure window decorations, transiency, and key bindings."""
        self.title(self._title_text)
        self.resizable(False, False)

        if self.master is not None and isinstance(
            self.master, (ctk.CTk, ctk.CTkToplevel)
        ):
            with suppress(tk.TclError):
                self.transient(self.master)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.bind("<Return>", lambda _e: self._on_default())
        if is_debug_mode():
            self.bind("<F12>", self._print_debug_telemetry)

    def _build_ui(self) -> None:
        """Construct the popup layout widgets."""
        self._main_frame = ctk.CTkFrame(
            self,
            corner_radius=self._corner_radius,
            border_width=self._border_width,
            border_color=self._border_color,
            fg_color=self._fg_color,
        )
        self._main_frame.pack(
            fill="both", expand=True, padx=POPUP_PADDING, pady=POPUP_PADDING
        )

        self._content_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        self._content_frame.pack(
            fill="both",
            expand=True,
            padx=CONTENT_PADDING_X,
            pady=CONTENT_PADDING_Y,
        )

        self._update_icon()
        self._update_text()

        self._button_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        self._button_frame.pack(
            fill="x",
            padx=BUTTON_CONTAINER_PADDING_X,
            pady=(0, BUTTON_CONTAINER_PADDING_BOTTOM),
        )

        self._button_container = ctk.CTkFrame(
            self._button_frame, fg_color="transparent"
        )
        self._button_container.pack(anchor="e")

        self._render_buttons()

    def _render_buttons(self) -> None:
        """Render action buttons inside the button container."""
        for button in self._action_buttons:
            with suppress(tk.TclError):
                button.destroy()
        self._action_buttons.clear()

        for button_spec in self._normalized_buttons:
            button = create_button(
                self._button_container,
                button_spec,
                on_click=self._on_button_click,
                role_colors=self.ROLE_COLORS,
            )
            button.pack(side="left", padx=BUTTON_SPACING)
            self._action_buttons.append(button)

    def _update_icon(self) -> None:
        """Display, update, or remove the dialog icon widget."""
        if self._icon_image is not None:
            if self._icon_label is None:
                self._icon_label = ctk.CTkLabel(
                    self._content_frame,
                    text="",
                    image=self._icon_image,
                )
                self._icon_label.pack(
                    side="left",
                    anchor="n",
                    padx=(0, ICON_PADDING_RIGHT),
                    pady=(ICON_PADDING_TOP, 0),
                )
            else:
                self._icon_label.configure(image=self._icon_image)
        elif self._icon_label is not None:
            self._icon_label.destroy()
            self._icon_label = None

    def _measure_text_height(
        self, text: str, wraplength: int, font: ctk.CTkFont | tuple[Any, ...] | None
    ) -> int:
        """Measure natural rendered height of wrapped text in logical pixels."""
        measurement_label = ctk.CTkLabel(
            self,
            text=text,
            wraplength=wraplength,
            justify="left",
            font=font,
        )
        measurement_label.update_idletasks()
        measured_height = unscale(self, measurement_label.winfo_reqheight())
        measurement_label.destroy()
        return measured_height

    def _update_text(self) -> None:
        """Render or update message text inside a label or scrollable text box."""
        message_font = (
            self._font
            if self._font is not None
            else ctk.CTkFont(size=MESSAGE_FONT_SIZE)
        )
        text_height = self._measure_text_height(
            self._text, self._wraplength, message_font
        )

        if text_height <= self._max_label_height:
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
                self._message_label.pack(
                    side="left", fill="both", expand=True, anchor="w"
                )
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
            if self._message_label is not None:
                self._message_label.destroy()
                self._message_label = None

            textbox_font = (
                self._font
                if (self._font is not None and "Traceback" not in self._text)
                else ctk.CTkFont(
                    family="Consolas" if "Traceback" in self._text else "Segoe UI",
                    size=TEXTBOX_FONT_SIZE,
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
        self, physical_width: int, physical_height: int
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
            target_x = (
                master.winfo_rootx() + (master.winfo_width() - physical_width) // 2
            )
            target_y = (
                master.winfo_rooty() + (master.winfo_height() - physical_height) // 2
            )
        else:
            screen_width, screen_height = scale(
                self, self.winfo_screenwidth(), self.winfo_screenheight()
            )
            target_x = (screen_width - physical_width) // 2
            target_y = (screen_height - physical_height) // 2

        return max(0, target_x), max(0, target_y)

    def _center_and_reveal(self, reposition: bool = True) -> None:
        """Calculate DPI-aware coordinates and reveal window without geometry jump."""
        self.update_idletasks()

        requested_width, requested_height = unscale(
            self, self.winfo_reqwidth(), self.winfo_reqheight()
        )
        final_base_width = max(requested_width, self._width)
        final_base_height = (
            self._height if self._height is not None else requested_height
        )

        final_physical_width, final_physical_height = scale(
            self, final_base_width, final_base_height
        )

        if reposition:
            target_x, target_y = self._calculate_coordinates(
                final_physical_width, final_physical_height
            )
            self.geometry(
                f"{final_base_width}x{final_base_height}+{target_x}+{target_y}"
            )
            self.deiconify()
            self.lift()
            self.focus_force()
        else:
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            self.geometry(
                f"{final_base_width}x{final_base_height}+{current_x}+{current_y}"
            )

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

    def _configure_dimensions(self, kwargs: dict[str, Any]) -> bool:
        """Configure dimension constraints and return True if geometry changed."""
        needs_regeometry = False
        if "width" in kwargs:
            self._width = int(kwargs.pop("width"))
            needs_regeometry = True
        if "height" in kwargs:
            val = kwargs.pop("height")
            self._height = int(val) if val is not None else None
            needs_regeometry = True
        return needs_regeometry

    def _configure_frame(self, kwargs: dict[str, Any]) -> None:
        """Configure outer frame styling."""
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

    def _configure_text(self, kwargs: dict[str, Any]) -> bool:
        """Configure text content, typography, and wrapping parameters."""
        text_changed = False

        if "text" in kwargs or "message" in kwargs:
            raw_text = kwargs.pop("text") if "text" in kwargs else kwargs.pop("message")
            self._text = str(raw_text)
            text_changed = True

        if "wraplength" in kwargs:
            self._wraplength = int(kwargs.pop("wraplength"))
            text_changed = True

        if "max_label_height" in kwargs:
            self._max_label_height = int(kwargs.pop("max_label_height"))
            text_changed = True

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            text_changed = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            if self._message_label is not None:
                self._message_label.configure(text_color=self._text_color)
            elif self._message_textbox is not None:
                self._message_textbox.configure(text_color=self._text_color)

        if text_changed:
            self._update_text()
            return True

        return False

    def _configure_icon(self, kwargs: dict[str, Any]) -> bool:
        """Configure icon image and return True if geometry changed."""
        if "icon" in kwargs:
            self._icon_input = kwargs.pop("icon")
            self._icon_image = resolve_icon(
                self._icon_input,
                preset_name=self._preset_key,
                display_size=ICON_DISPLAY_SIZE,
            )
            self._update_icon()
            return True
        return False

    def _configure_buttons(self, kwargs: dict[str, Any]) -> bool:
        """Configure buttons and action defaults."""
        needs_regeometry = False
        if "buttons" in kwargs:
            self._raw_buttons = kwargs.pop("buttons")
            self._normalized_buttons = normalize_buttons(self._raw_buttons)
            self._render_buttons()
            needs_regeometry = True
        if "default_button" in kwargs:
            self._default_value = kwargs.pop("default_button")
        if "cancel_button" in kwargs:
            self._cancel_value = kwargs.pop("cancel_button")
        return needs_regeometry

    def _configure_preset(self, kwargs: dict[str, Any]) -> bool:
        """Apply preset configuration defaults."""
        if "preset" not in kwargs:
            return False

        preset_name = kwargs.pop("preset")
        if preset_name not in self.PRESETS:
            return False

        self._preset = preset_name
        self._preset_key = preset_name
        preset_config = self.PRESETS[preset_name]

        if "title" not in kwargs and preset_config.get("title"):
            self._title_text = _format_window_title(str(preset_config["title"]))
            self.title(self._title_text)

        if "icon" not in kwargs and preset_config.get("icon"):
            self._icon_input = preset_config["icon"]
            self._icon_image = resolve_icon(
                self._icon_input,
                preset_name=self._preset_key,
                display_size=ICON_DISPLAY_SIZE,
            )
            self._update_icon()

        if "buttons" not in kwargs and preset_config.get("buttons"):
            self._raw_buttons = preset_config["buttons"]
            self._normalized_buttons = normalize_buttons(self._raw_buttons)
            self._render_buttons()

        if "default_button" not in kwargs and "default_button" in preset_config:
            self._default_value = preset_config["default_button"]

        if "cancel_button" not in kwargs and "cancel_button" in preset_config:
            self._cancel_value = preset_config["cancel_button"]

        return True

    @override
    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        """Update popup configuration options and refresh child widgets.

        Args:
            require_redraw: Passed to superclass configure if needed.
            **kwargs: Configuration options to update ('text', 'title', 'icon', etc.).
        """
        needs_regeometry = False

        if "title" in kwargs:
            self._title_text = _format_window_title(str(kwargs.pop("title")))
            self.title(self._title_text)

        needs_regeometry |= self._configure_dimensions(kwargs)
        self._configure_frame(kwargs)
        needs_regeometry |= self._configure_text(kwargs)
        needs_regeometry |= self._configure_icon(kwargs)
        needs_regeometry |= self._configure_buttons(kwargs)
        needs_regeometry |= self._configure_preset(kwargs)

        if "sound" in kwargs:
            self._sound = bool(kwargs.pop("sound"))

        if "callback" in kwargs:
            self._callback = kwargs.pop("callback")

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
        """Save the chosen return value, release modal grab, and destroy dialog."""
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
