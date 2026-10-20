"""Runtime telemetry and debug tools for CustomTkinter windows."""

from typing import Any

from ctkforge.geometry import unscale

DEBUG_BANNER: str = " === DEBUG MODE IS ACTIVE ==="
_DEBUG_ACTIVE: bool = False

__all__ = [
    "DEBUG_BANNER",
    "enable_debug_mode",
    "is_debug_mode",
    "print_window_telemetry",
]


def is_debug_mode() -> bool:
    """Return whether debug mode is currently active across the application."""
    return _DEBUG_ACTIVE


def print_window_telemetry(window: Any) -> None:
    """Print size, DPI scaling, and baseline dimensions for the active window.

    Args:
        window: The active Tk or CustomTkinter window to inspect.
    """
    if not hasattr(window, "winfo_exists") or not window.winfo_exists():
        return

    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    base_w, base_h = unscale(window, width, height)
    base_req_w, base_req_h = unscale(
        window, window.winfo_reqwidth(), window.winfo_reqheight()
    )
    scaling = (
        window._get_window_scaling()
        if hasattr(window, "_get_window_scaling")
        else getattr(window, "_get_widget_scaling", lambda: 1.0)()
    )

    # Resolve window title
    title_text = (
        window.title()
        if callable(getattr(window, "title", None))
        else getattr(window, "_title_text", "Untitled")
    )

    class_name = window.__class__.__name__

    print(f"\n--- {class_name} Telemetry ---")
    print(f"Title:         {title_text}")
    print(
        f"Physical Size: {width}x{height} px @ {scaling:g} ({int(scaling * 100)}%) Scaling"
    )
    print(f"Baseline Size: {base_w}x{base_h} px (96 DPI)")
    if hasattr(window, "_target_width"):
        print(f"Target Width:  {window._target_width} px")
    print(
        f"Req Size:      {base_req_w}x{base_req_h} px (base) / {window.winfo_reqwidth()}x{window.winfo_reqheight()} px (phys)"
    )
    print("-" * (len(class_name) + 18) + "\n")


def enable_debug_mode(app: Any, banner: str = DEBUG_BANNER) -> None:
    """Activate debug mode across the application, popups, and future windows.

    This function:
      1. Sets the global debug state to active.
      2. Appends the debug banner to the root application window title.
      3. Binds <F12> globally so pressing F12 in any focused window prints its telemetry.

    Args:
        app: The root CTk or CTkToplevel application instance.
        banner: Text appended to the window title to show debug is active.
    """
    global _DEBUG_ACTIVE
    _DEBUG_ACTIVE = True

    # Append banner to app title if not already present
    if hasattr(app, "title") and callable(app.title):
        current_title = app.title()
        if banner not in current_title:
            app.title(f"{current_title}{banner}")

    def _handle_f12(event: Any) -> None:
        target_window = event.widget.winfo_toplevel()
        print_window_telemetry(target_window)

    # Bind globally so whichever window has focus receives the F12 telemetry dump
    if hasattr(app, "bind_all") and callable(app.bind_all):
        app.bind_all("<F12>", _handle_f12)
