"""DPI-aware geometry, scaling, and coordinate conversion helpers for CustomTkinter."""

from typing import Any, overload

__all__ = ["scale", "unscale"]


def _get_scaling(target: Any) -> float:
    """Safely extract active DPI scaling factor from a CTk widget or window.

    CustomTkinter defines `_get_window_scaling()` on CTkBaseClass, so `hasattr`
    returns True for all widgets. However, the underlying private `__window_scaling`
    attribute only exists on root `CTk` windows. Calling it on child widgets raises
    AttributeError. We inspect `_get_widget_scaling` first and safely catch
    AttributeError if `_get_window_scaling` is called on a child widget.
    """
    for method_name in ("_get_widget_scaling", "_get_window_scaling"):
        method = getattr(target, method_name, None)
        if callable(method):
            try:
                val = method()
                if isinstance(val, (int, float)) and val > 0:
                    return float(val)
            except AttributeError:
                continue
    return 1.0


@overload
def unscale(target: Any, value: float, /) -> int: ...


@overload
def unscale(
    target: Any,
    value1: float,
    value2: float,
    /,
    *values: float,
) -> tuple[int, ...]: ...


def unscale(target: Any, *values: float) -> int | tuple[int, ...]:
    """Convert physical (device hardware) pixel values to logical (96 DPI baseline) integers.

    Args:
        target: A CTk widget or window providing the active DPI scaling factor.
        *values: One or more physical pixel values to convert to logical units.

    Returns:
        A single logical integer if one value was provided, or a tuple of logical integers if multiple.

    Raises:
        ValueError: If no values are passed.
    """
    if not values:
        raise ValueError("unscale() requires at least one value to convert.")

    scaling = _get_scaling(target)
    result = tuple(round(v / scaling) if scaling else round(v) for v in values)
    return result[0] if len(result) == 1 else result


@overload
def scale(target: Any, value: float, /) -> int: ...


@overload
def scale(
    target: Any,
    value1: float,
    value2: float,
    /,
    *values: float,
) -> tuple[int, ...]: ...


def scale(target: Any, *values: float) -> int | tuple[int, ...]:
    """Convert logical (96 DPI baseline) pixel values to physical (device hardware) integers.

    Args:
        target: A CTk widget or window providing the active DPI scaling factor.
        *values: One or more logical pixel values to convert to physical device units.

    Returns:
        A single physical integer if one value was provided, or a tuple of physical integers if multiple.

    Raises:
        ValueError: If no values are passed.
    """
    if not values:
        raise ValueError("scale() requires at least one value to convert.")

    scaling = _get_scaling(target)
    result = tuple(round(v * scaling) if scaling else round(v) for v in values)
    return result[0] if len(result) == 1 else result
