"""Tkinter GUI client for the batteries server.

Run:
    py client.py
"""

import json
import socket
import tkinter as tk
from tkinter import ttk, messagebox

HOST = "127.0.0.1"
PORT = 5050


class BatteryClient:
    """Thin JSON-line client over a persistent TCP socket."""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = None
        self.f = None
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self.f = self.sock.makefile("rwb")

    def call(self, **req):
        self.f.write((json.dumps(req) + "\n").encode("utf-8"))
        self.f.flush()
        line = self.f.readline()
        if not line:
            raise ConnectionError("server closed connection")
        return json.loads(line.decode("utf-8"))

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass


class App(tk.Tk):
    COLS = (
        "id", "name", "manufacturer", "chemistry", "form_factor",
        "capacity_mah", "voltage_v", "weight_g", "rechargeable",
        "year_introduced",
    )

    def __init__(self):
        super().__init__()
        self.title("Battery Browser")
        self.geometry("1050x600")
        self.alive = True

        try:
            self.client = BatteryClient()
        except Exception as e:
            self.alive = False
            self.withdraw()
            messagebox.showerror(
                "Connection failed",
                f"Could not connect to {HOST}:{PORT}\n\n{e}\n\n"
                "Make sure server.py is running.",
            )
            self.destroy()
            return

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.refresh()

    def _build_ui(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")

        ttk.Label(bar, text="Chemistry:").pack(side="left")
        self.chem_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.chem_var, width=14).pack(side="left", padx=(2, 10))

        ttk.Label(bar, text="Form factor:").pack(side="left")
        self.form_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.form_var, width=10).pack(side="left", padx=(2, 10))

        ttk.Label(bar, text="Min mAh:").pack(side="left")
        self.min_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.min_var, width=8).pack(side="left", padx=(2, 10))

        ttk.Button(bar, text="Search",   command=self.search).pack(side="left")
        ttk.Button(bar, text="Show all", command=self.refresh).pack(side="left", padx=4)
        ttk.Button(bar, text="Stats",    command=self.show_stats).pack(side="left", padx=4)

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=8)

        self.tree = ttk.Treeview(frame, columns=self.COLS, show="headings")
        widths = {
            "id": 40, "name": 200, "manufacturer": 110, "chemistry": 100,
            "form_factor": 90, "capacity_mah": 90, "voltage_v": 70,
            "weight_g": 70, "rechargeable": 90, "year_introduced": 70,
        }
        for c in self.COLS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 80), anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Add battery...", command=self.add_dialog).pack(side="left")
        ttk.Button(bottom, text="Delete selected", command=self.delete_selected).pack(side="left", padx=4)

        self.status = tk.StringVar(value="Connected.")
        ttk.Label(bottom, textvariable=self.status, anchor="e").pack(side="right", fill="x", expand=True)

    # ---- server actions ----
    def refresh(self):
        try:
            r = self.client.call(action="list")
        except Exception as e:
            self.status.set(f"Error: {e}")
            return
        self._populate(r.get("rows", []))

    def search(self):
        req = {"action": "search"}
        if self.chem_var.get().strip(): req["chemistry"]   = self.chem_var.get().strip()
        if self.form_var.get().strip(): req["form_factor"] = self.form_var.get().strip()
        if self.min_var.get().strip():
            try:
                req["min_capacity"] = int(self.min_var.get().strip())
            except ValueError:
                messagebox.showwarning("Invalid input", "Min mAh must be an integer.")
                return
        try:
            r = self.client.call(**req)
        except Exception as e:
            self.status.set(f"Error: {e}")
            return
        self._populate(r.get("rows", []))

    def add_dialog(self):
        AddDialog(self, on_save=self._do_add)

    def _do_add(self, data):
        try:
            r = self.client.call(action="add", data=data)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if r.get("ok"):
            self.status.set(f"Added id {r['id']}")
            self.refresh()
        else:
            messagebox.showerror("Server error", r.get("error", "unknown"))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        row_id = int(self.tree.item(sel[0], "values")[0])
        if not messagebox.askyesno("Confirm delete", f"Delete battery id {row_id}?"):
            return
        try:
            r = self.client.call(action="delete", id=row_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if r.get("ok"):
            self.status.set(f"Deleted {r['deleted']} row(s)")
            self.refresh()

    def show_stats(self):
        try:
            r = self.client.call(action="stats")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        rows = r.get("rows", [])
        text = f"{'Chemistry':<14} {'Count':>5}  {'Avg mAh':>9}  {'Avg V':>5}\n" + "-" * 40 + "\n"
        for row in rows:
            text += (
                f"{str(row['chemistry']):<14} "
                f"{row['count']:>5}  "
                f"{str(row['avg_capacity_mah']):>9}  "
                f"{str(row['avg_voltage_v']):>5}\n"
            )
        messagebox.showinfo("Stats by chemistry", text)

    # ---- helpers ----
    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            vals = [row.get(c, "") for c in self.COLS]
            self.tree.insert("", "end", values=vals)
        self.status.set(f"{len(rows)} row(s)")

    def _on_close(self):
        self.client.close()
        self.destroy()


class AddDialog(tk.Toplevel):
    FIELDS = [
        ("name",            "Name",            str),
        ("manufacturer",    "Manufacturer",    str),
        ("chemistry",       "Chemistry",       str),
        ("form_factor",     "Form factor",     str),
        ("capacity_mah",    "Capacity (mAh)",  int),
        ("voltage_v",       "Voltage (V)",     float),
        ("weight_g",        "Weight (g)",      float),
        ("year_introduced", "Year introduced", int),
        ("notes",           "Notes",           str),
    ]

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Add battery")
        self.on_save = on_save
        self.vars = {}
        for i, (key, label, _t) in enumerate(self.FIELDS):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="e", padx=6, pady=2)
            v = tk.StringVar()
            ttk.Entry(self, textvariable=v, width=30).grid(row=i, column=1, padx=6, pady=2)
            self.vars[key] = v
        self.rech_var = tk.IntVar()
        ttk.Checkbutton(self, text="Rechargeable", variable=self.rech_var).grid(
            row=len(self.FIELDS), column=1, sticky="w", padx=6, pady=2,
        )
        ttk.Button(self, text="Save", command=self._save).grid(
            row=len(self.FIELDS) + 1, column=1, sticky="e", padx=6, pady=8,
        )

    def _save(self):
        data = {"rechargeable": bool(self.rech_var.get())}
        for key, label, t in self.FIELDS:
            raw = self.vars[key].get().strip()
            if not raw:
                data[key] = None
                continue
            try:
                data[key] = raw if t is str else t(raw)
            except ValueError:
                messagebox.showwarning("Invalid input", f"{label} must be {t.__name__}.")
                return
        if not data.get("name") or not data.get("chemistry"):
            messagebox.showwarning("Missing", "Name and chemistry are required.")
            return
        self.on_save(data)
        self.destroy()


def main():
    app = App()
    if app.alive:
        app.mainloop()


if __name__ == "__main__":
    main()
