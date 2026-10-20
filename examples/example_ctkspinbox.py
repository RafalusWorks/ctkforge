import customtkinter as ctk

from ctkforge import CTkSpinbox

app = ctk.CTk()
app.geometry("320x180")
app.title("CTkSpinbox Demo")

status_label = ctk.CTkLabel(app, text="Current value: 25")
status_label.pack(pady=(25, 10))


def on_change(value: int) -> None:
    status_label.configure(text=f"Current value: {value}")


spinbox = CTkSpinbox(
    master=app,
    start_value=25,
    min_value=0,
    max_value=100,
    step=5,
    command=on_change,
)
spinbox.pack(pady=10)


def on_closing() -> None:
    """Stop the event loop immediately and destroy window resources."""
    app.quit()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()

