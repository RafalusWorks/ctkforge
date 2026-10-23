"""Comprehensive automated test suite for CTkSpinbox."""

from __future__ import annotations

import customtkinter as ctk

from ctkforge import CTkSpinbox


def run_spinbox_test_suite(
    spinbox: CTkSpinbox,
    root: ctk.CTk,
) -> None:
    """Execute all 16 automated tests on a spinbox instance."""

    def step() -> None:
        root.update()

    def clean_slate_reset() -> None:
        """Reset the spinbox to its baseline state."""
        spinbox.configure(
            min_value=0,
            max_value=100,
            step=5,
            state="normal",
            command=None,
            height=28,
            justify="center",
        )
        spinbox.set(25)
        root.update()

    clean_slate_reset()

    # 1. Initial State & Inspection Properties
    step()
    assert spinbox.get() == 25, f"[1/16 Failed] Expected 25, got {spinbox.get()}"
    assert spinbox.min_value == 0, f"[1/16 Failed] min_value is {spinbox.min_value}"
    assert spinbox.max_value == 100, f"[1/16 Failed] max_value is {spinbox.max_value}"
    assert spinbox.step == 5, f"[1/16 Failed] step is {spinbox.step}"
    assert spinbox.entry.get() == "25", f"[1/16 Failed] Entry text is {spinbox.entry.get()}"
    print("[1/16] Initial State & Inspection Properties: PASSED")

    # 2. Direct Value Set & Get
    step()
    spinbox.set(45)
    assert spinbox.get() == 45, f"[2/16 Failed] Expected 45, got {spinbox.get()}"
    assert spinbox.entry.get() == "45", f"[2/16 Failed] Entry text is {spinbox.entry.get()}"
    spinbox.set(0)
    assert spinbox.get() == 0, f"[2/16 Failed] Expected 0, got {spinbox.get()}"
    print("[2/16] Direct Value Set & Get: PASSED")

    # 3. Boundary Clamping on .set()
    step()
    spinbox.set(-50)
    assert spinbox.get() == 0, f"[3/16 Failed] Lower clamp failed: {spinbox.get()}"
    assert spinbox.entry.get() == "0", f"[3/16 Failed] Entry mismatch on lower clamp: {spinbox.entry.get()}"
    spinbox.set(999)
    assert spinbox.get() == 100, f"[3/16 Failed] Upper clamp failed: {spinbox.get()}"
    assert spinbox.entry.get() == "100", f"[3/16 Failed] Entry mismatch on upper clamp: {spinbox.entry.get()}"
    print("[3/16] Boundary Clamping on .set(): PASSED")

    # 4. Step Increments & Decrements
    step()
    spinbox.set(20)
    spinbox._increment()
    assert spinbox.get() == 25, f"[4/16 Failed] Increment failed: {spinbox.get()}"
    spinbox._increment()
    assert spinbox.get() == 30, f"[4/16 Failed] Increment failed: {spinbox.get()}"
    spinbox._decrement()
    assert spinbox.get() == 25, f"[4/16 Failed] Decrement failed: {spinbox.get()}"
    print("[4/16] Step Increments & Decrements: PASSED")

    # 5. Boundary Saturation on Stepping
    step()
    spinbox.set(98)
    spinbox._increment()
    assert spinbox.get() == 100, f"[5/16 Failed] Expected clamp at 100, got {spinbox.get()}"
    spinbox._increment()
    assert spinbox.get() == 100, f"[5/16 Failed] Upper saturation failed: {spinbox.get()}"
    spinbox.set(2)
    spinbox._decrement()
    assert spinbox.get() == 0, f"[5/16 Failed] Expected clamp at 0, got {spinbox.get()}"
    spinbox._decrement()
    assert spinbox.get() == 0, f"[5/16 Failed] Lower saturation failed: {spinbox.get()}"
    print("[5/16] Boundary Saturation on Stepping: PASSED")

    # 6. Command Callback Notification
    step()
    callback_log: list[int] = []

    def on_change(val: int) -> None:
        """Record value received by callback."""
        callback_log.append(val)

    spinbox.configure(command=on_change)
    spinbox.set(50)
    assert callback_log == [50], f"[6/16 Failed] Callback log is {callback_log}"
    spinbox._increment()
    assert callback_log == [50, 55], f"[6/16 Failed] Callback log is {callback_log}"
    spinbox._decrement()
    assert callback_log == [50, 55, 50], f"[6/16 Failed] Callback log is {callback_log}"
    spinbox.configure(command=None)
    print("[6/16] Command Callback Notification: PASSED")

    # 7. Text Entry Typing & <Return> Commit
    step()
    spinbox.entry.delete(0, "end")
    spinbox.entry.insert(0, "65")
    spinbox._on_entry_changed()
    assert spinbox.get() == 65, f"[7/16 Failed] Expected 65 from entry, got {spinbox.get()}"
    print("[7/16] Text Entry Typing & <Return> Commit: PASSED")

    # 8. Text Entry Parsing Fallback
    step()
    spinbox.set(40)
    spinbox.entry.delete(0, "end")
    spinbox.entry.insert(0, "invalid_text")
    spinbox._on_entry_changed()
    assert spinbox.get() == 40, f"[8/16 Failed] Fallback failed on bad string: {spinbox.get()}"
    assert spinbox.entry.get() == "40", f"[8/16 Failed] Entry text did not revert: {spinbox.entry.get()}"
    spinbox.entry.delete(0, "end")
    spinbox.entry.insert(0, "   ")
    spinbox._on_entry_changed()
    assert spinbox.get() == 40, f"[8/16 Failed] Fallback failed on blank string: {spinbox.get()}"
    assert spinbox.entry.get() == "40", f"[8/16 Failed] Entry text did not revert: {spinbox.entry.get()}"
    print("[8/16] Text Entry Parsing Fallback: PASSED")

    # 9. Text Entry Out-of-Bounds Clamping
    step()
    spinbox.entry.delete(0, "end")
    spinbox.entry.insert(0, "750")
    spinbox._on_entry_changed()
    assert spinbox.get() == 100, f"[9/16 Failed] Expected upper clamp at 100, got {spinbox.get()}"
    assert spinbox.entry.get() == "100", f"[9/16 Failed] Entry text is {spinbox.entry.get()}"
    spinbox.entry.delete(0, "end")
    spinbox.entry.insert(0, "-120")
    spinbox._on_entry_changed()
    assert spinbox.get() == 0, f"[9/16 Failed] Expected lower clamp at 0, got {spinbox.get()}"
    assert spinbox.entry.get() == "0", f"[9/16 Failed] Entry text is {spinbox.entry.get()}"
    print("[9/16] Text Entry Out-of-Bounds Clamping: PASSED")

    # 10. Dynamic .configure() and .cget()
    step()
    spinbox.set(50)
    spinbox.configure(min_value=10, max_value=40, step=2)
    assert spinbox.cget("min_value") == 10, f"[10/16 Failed] cget min_value failed: {spinbox.cget('min_value')}"
    assert spinbox.cget("max_value") == 40, f"[10/16 Failed] cget max_value failed: {spinbox.cget('max_value')}"
    assert spinbox.cget("step") == 2, f"[10/16 Failed] cget step failed: {spinbox.cget('step')}"
    assert spinbox.get() == 40, f"[10/16 Failed] Auto-clamp on boundary change failed: {spinbox.get()}"
    spinbox.configure(min_value=0, max_value=100, step=5)
    print("[10/16] Dynamic .configure() and .cget(): PASSED")

    # 11. Disabled State Enforcement
    step()
    spinbox.set(30)
    spinbox.configure(state="disabled")
    assert spinbox.cget("state") == "disabled", "[11/16 Failed] State is not disabled"
    spinbox._increment()
    assert spinbox.get() == 30, f"[11/16 Failed] Increment allowed while disabled: {spinbox.get()}"
    spinbox._decrement()
    assert spinbox.get() == 30, f"[11/16 Failed] Decrement allowed while disabled: {spinbox.get()}"
    spinbox._on_entry_changed()
    assert spinbox.get() == 30, f"[11/16 Failed] Entry change allowed while disabled: {spinbox.get()}"
    spinbox.configure(state="normal")
    assert spinbox.cget("state") == "normal", "[11/16 Failed] State is not normal"
    spinbox._increment()
    assert spinbox.get() == 35, f"[11/16 Failed] Increment failed after restore: {spinbox.get()}"
    print("[11/16] Disabled State Enforcement: PASSED")

    # 12. MouseWheel Event Simulation
    step()
    spinbox.set(50)

    class FakeWheelEvent:
        """Minimal mock event carrying a delta attribute."""

        def __init__(self, delta: int) -> None:
            self.delta = delta

    spinbox._on_mousewheel(FakeWheelEvent(120))
    assert spinbox.get() == 55, f"[12/16 Failed] Wheel up failed: {spinbox.get()}"
    spinbox._on_mousewheel(FakeWheelEvent(-120))
    assert spinbox.get() == 50, f"[12/16 Failed] Wheel down failed: {spinbox.get()}"
    print("[12/16] MouseWheel Event Simulation: PASSED")

    # 13. Keyboard Arrow Event Bindings
    step()
    spinbox.set(50)
    spinbox.entry._entry.focus_force()
    root.update()
    spinbox.entry._entry.event_generate("<Key-Up>", keysym="Up")
    root.update()
    assert spinbox.get() == 55, f"[13/16 Failed] Key <Up> failed: {spinbox.get()}"
    spinbox.entry._entry.event_generate("<Key-Down>", keysym="Down")
    root.update()
    assert spinbox.get() == 50, f"[13/16 Failed] Key <Down> failed: {spinbox.get()}"
    print("[13/16] Keyboard Arrow Event Bindings: PASSED")

    # 14. Visual Geometry & Button Proportion Recalculation
    step()
    spinbox.configure(height=36)
    root.update()
    btn_w, btn_h, _ = spinbox._calculate_button_geometry(36)
    assert spinbox._up_button.cget("height") == btn_h, "[14/16 Failed] Up button height not resized"
    assert spinbox._up_button.cget("width") == btn_w, "[14/16 Failed] Up button width not resized"
    spinbox.configure(height=28)
    print("[14/16] Visual Geometry & Button Proportion Recalculation: PASSED")

    # 15. Focus Delegation
    step()
    spinbox.focus()
    root.update()
    spinbox.focus_set()
    root.update()
    print("[15/16] Focus Delegation: PASSED")

    # 16. State Reset & Teardown Cleanliness
    step()
    clean_slate_reset()
    assert spinbox.get() == 25, f"[16/16 Failed] Reset value is {spinbox.get()}"
    assert spinbox.min_value == 0, f"[16/16 Failed] Reset min_value is {spinbox.min_value}"
    assert spinbox.max_value == 100, f"[16/16 Failed] Reset max_value is {spinbox.max_value}"
    assert spinbox.step == 5, f"[16/16 Failed] Reset step is {spinbox.step}"
    assert spinbox.cget("state") == "normal", f"[16/16 Failed] Reset state is {spinbox.cget('state')}"
    print("[16/16] State Reset & Teardown Cleanliness: PASSED")


def run_headless_tests() -> None:
    """Run automated verification checks headlessly and exit."""
    print("Running automated sanity tests for CTkSpinbox (headless)...")
    root = ctk.CTk()
    root.geometry("400x300")

    spinbox = CTkSpinbox(root, start_value=25, min_value=0, max_value=100, step=5)
    spinbox.pack(padx=20, pady=20)
    root.update()

    run_spinbox_test_suite(spinbox, root)
    root.destroy()
    print("All automated checks (16/16) passed successfully!")


def test_ctkspinbox() -> None:
    """Entry point for automated pytest test runner discovery."""
    run_headless_tests()


if __name__ == "__main__":
    run_headless_tests()
