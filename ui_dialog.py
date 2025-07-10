import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from types import SimpleNamespace
from datetime import datetime, timezone

def get_parameters_via_dialog():
    class ParamDialog:
        def __init__(self, parent):
            self.result = None
            self.top = tk.Toplevel(parent)
            self.top.title("Calendar to Clockify Parameters")
            self.top.grab_set()
            self.top.protocol("WM_DELETE_WINDOW", self.cancel)
            # Start date
            ttk.Label(self.top, text="Start date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.start_cal = DateEntry(self.top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            self.start_cal.set_date(datetime.now())
            self.start_cal.grid(row=0, column=1, padx=5, pady=5)
            # End date
            ttk.Label(self.top, text="End date:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.end_cal = DateEntry(self.top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            self.end_cal.set_date(datetime.now())
            self.end_cal.grid(row=1, column=1, padx=5, pady=5)
            # Simulate checkbox
            self.simulate_var = tk.BooleanVar()
            self.simulate_cb = ttk.Checkbutton(self.top, text="Simulate (preview only)", variable=self.simulate_var)
            self.simulate_cb.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
            # Purge checkbox
            self.purge_var = tk.BooleanVar()
            self.purge_cb = ttk.Checkbutton(self.top, text="Purge (delete bot entries)", variable=self.purge_var)
            self.purge_cb.grid(row=3, column=0, columnspan=2, sticky="w", padx=5)
            # Buttons
            btn_frame = ttk.Frame(self.top)
            btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
            ttk.Button(btn_frame, text="OK", command=self.ok).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side="left", padx=5)
            self.top.bind('<Return>', lambda event: self.ok())
            self.top.bind('<Escape>', lambda event: self.cancel())
        def ok(self):
            start = self.start_cal.get_date().strftime("%Y-%m-%d")
            end = self.end_cal.get_date().strftime("%Y-%m-%d")
            simulate = self.simulate_var.get()
            purge = self.purge_var.get()
            # Validate dates
            try:
                start_date = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                end_date = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                messagebox.showerror("Input Error", "Start and end dates must be in YYYY-MM-DD format.")
                return
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.")
                return
            if (end_date - start_date).days > 31:
                messagebox.showerror("Input Error", "Date range cannot exceed 31 days.")
                return
            self.result = SimpleNamespace(
                start=start,
                end=end,
                simulate=simulate,
                purge=purge
            )
            self.top.destroy()
        def cancel(self):
            self.result = None
            self.top.destroy()
    root = tk.Tk()
    root.withdraw()
    dialog = ParamDialog(root)
    root.wait_window(dialog.top)
    if dialog.result is None:
        return None
    return dialog.result 