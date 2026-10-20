"""Comprehensive test and demonstration script for CTkPopup."""

from __future__ import annotations

import time
from typing import Any

import customtkinter as ctk

from ctkforge import CTkPopup


def run_popup_test_suite(root: ctk.CTk, visual: bool = False) -> None:
    """Execute automated tests verifying CTkPopup CustomTkinter convention compliance."""

    def step(delay: float = 0.2) -> None:
        if visual:
            root.update()
            time.sleep(delay)

    # 1. Verification of CTk Naming Convention: 'text' parameter and .cget()
    step()
    popup = CTkPopup(
        master=root,
        title="Verification Dialog",
        text="Initial text prompt",
        preset="info",
    )
    root.update()
    assert popup.cget("text") == "Initial text prompt", f"[1/10 Failed] text is {popup.cget('text')}"
    assert popup.cget("message") == "Initial text prompt", f"[1/10 Failed] message alias is {popup.cget('message')}"
    assert popup.cget("title") == "Verification Dialog", f"[1/10 Failed] title is {popup.cget('title')}"
    assert popup.cget("preset") == "info", f"[1/10 Failed] preset is {popup.cget('preset')}"
    print("[1/10] CTk Standard 'text' parameter and .cget() inspection: PASSED")

    # 2. No arbitrary property setters / getters on widget
    step()
    assert not hasattr(type(popup), "height") or not isinstance(getattr(type(popup), "height", None), property), (
        "[2/10 Failed] CTkPopup should not expose height property"
    )
    assert not hasattr(type(popup), "text") or not isinstance(getattr(type(popup), "text", None), property), (
        "[2/10 Failed] CTkPopup should not expose text property"
    )
    print("[2/10] Clean CTk encapsulation (no arbitrary property getters/setters): PASSED")

    # 3. Dynamic .configure(text=...) updates
    step()
    popup.configure(text="Updated short prompt text")
    root.update()
    assert popup.cget("text") == "Updated short prompt text", "[3/10 Failed] .configure(text=...) failed"
    print("[3/10] Dynamic .configure(text=...): PASSED")

    # 4. Dynamic .configure(title=...) updates
    step()
    popup.configure(title="New Title Header")
    root.update()
    assert "New Title Header" in popup.cget("title"), "[4/10 Failed] .configure(title=...) failed"
    print("[4/10] Dynamic .configure(title=...): PASSED")

    # 5. Styling options via .configure() (border_width, border_color, fg_color)
    step()
    popup.configure(border_width=3, border_color="#10B981", fg_color="#1E293B")
    root.update()
    assert popup.cget("border_width") == 3, "[5/10 Failed] border_width not updated"
    assert popup.cget("border_color") == "#10B981", "[5/10 Failed] border_color not updated"
    assert popup.cget("fg_color") == "#1E293B", "[5/10 Failed] fg_color not updated"
    print("[5/10] Styling options via .configure(): PASSED")

    # 6. Automatic upgrade from CTkLabel to CTkTextbox on long text
    step()
    long_traceback = "Traceback (most recent call last):\n" + "\n".join([f"  File 'module_{i}.py', line {i*10}, in func_{i}" for i in range(25)])
    popup.configure(text=long_traceback)
    root.update()
    assert popup._message_textbox is not None, "[6/10 Failed] Expected switch to CTkTextbox for long text"
    assert popup._message_label is None, "[6/10 Failed] Expected CTkLabel to be destroyed"
    print("[6/10] Dynamic transition to CTkTextbox for tall text: PASSED")

    # 7. Automatic downgrade from CTkTextbox back to CTkLabel on short text
    step()
    popup.configure(text="Back to brief message")
    root.update()
    assert popup._message_label is not None, "[7/10 Failed] Expected switch back to CTkLabel for short text"
    assert popup._message_textbox is None, "[7/10 Failed] Expected CTkTextbox to be destroyed"
    print("[7/10] Dynamic transition back to CTkLabel for brief text: PASSED")

    # 8. Dynamic reconfiguration of action buttons
    step()
    popup.configure(buttons=[{"label": "Confirm", "value": "confirmed", "role": "primary"}, {"label": "Abort", "value": "aborted", "role": "cancel"}])
    root.update()
    assert len(popup._action_buttons) == 2, f"[8/10 Failed] Expected 2 action buttons, got {len(popup._action_buttons)}"
    print("[8/10] Dynamic button reconfiguration via .configure(buttons=...): PASSED")

    # 9. Button click execution and Courier Rule cleanup
    step()
    popup._on_button_click("confirmed")
    root.update()
    assert popup.get() == "confirmed", f"[9/10 Failed] Expected 'confirmed', got {popup.get()}"
    print("[9/10] Button execution and .get() result retrieval: PASSED")

    # 10. Non-blocking callback lifecycle and keyboard escape
    step()
    callback_result: list[Any] = []
    cb_popup = CTkPopup(
        master=root,
        title="Callback Test",
        text="Pressing escape should trigger cancel",
        buttons=["OK", "Cancel"],
        callback=lambda res: callback_result.append(res),
    )
    root.update()
    cb_popup._on_cancel()
    root.update()
    assert callback_result == [cb_popup.cget("cancel_button")], f"[10/10 Failed] Callback received {callback_result}"
    print("[10/10] Non-blocking callback and cancel protocol: PASSED")


def run_headless_tests() -> None:
    """Run test suite headlessly without opening persistent windows."""
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.geometry("400x300")
    root.withdraw()
    root.update()

    print("Running automated sanity tests for CTkPopup (headless)...")
    run_popup_test_suite(root, visual=False)
    root.destroy()
    print("All automated checks (10/10) passed successfully!")


if __name__ == "__main__":
    run_headless_tests()
