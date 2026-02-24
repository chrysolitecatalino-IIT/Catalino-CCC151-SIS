import tkinter as tk
from tkinter import ttk, messagebox

from config import COLLEGE_FILE, COLLEGE_FIELDS, PROGRAM_FILE
from utils import load_data, save_data


COL_WIDTHS = [80, 300]
LABELS     = ["Code", "Name"]


class CollegeTab:

    def __init__(self, notebook):
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Colleges")
        self._editing_code = None
        self._build_ui()
        self.tab.after(100, self.refresh)

    def _build_ui(self):
        form = tk.LabelFrame(self.tab, text="College Details", padx=8, pady=8)
        form.pack(fill="x", padx=10, pady=(10, 0))

        self.entries = {}
        field_labels = ["Code", "Name"]
        for i, (field, label) in enumerate(zip(COLLEGE_FIELDS, field_labels)):
            tk.Label(form, text=label).grid(row=0, column=i * 2, padx=6, pady=4, sticky="e")
            entry = tk.Entry(form, width=25)
            entry.grid(row=0, column=i * 2 + 1, padx=6, sticky="w")
            self.entries[field] = entry

        btn_frame = tk.Frame(self.tab)
        btn_frame.pack(pady=6)
        self.save_edit_btn = tk.Button(btn_frame, text="Save Edit", width=9,
                                       command=self._commit_edit,
                                       bg="#5cb85c", fg="white")
        # not packed yet — only shown when editing
        tk.Button(btn_frame, text="Add",   width=9, command=self.add).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Clear", width=9, command=self._clear).pack(side="left", padx=4)

        # table header
        header = tk.Frame(self.tab, bg="#3c3f41")
        header.pack(fill="x", padx=10)
        for i, (lbl, w) in enumerate(zip(LABELS, COL_WIDTHS)):
            tk.Label(header, text=lbl, bg="#3c3f41", fg="white",
                     width=w // 7, anchor="w").grid(row=0, column=i, padx=4, pady=3)
        tk.Label(header, text="Actions", bg="#3c3f41", fg="white",
                 width=10, anchor="w").grid(row=0, column=len(LABELS), padx=4)

        container = tk.Frame(self.tab)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.rows_frame = tk.Frame(canvas)
        self.canvas_window = canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.rows_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.canvas_window, width=e.width))

        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>",   _on_mousewheel)
            widget.bind("<Button-5>",   _on_mousewheel)

        self._bind_mousewheel = _bind_mousewheel
        _bind_mousewheel(canvas)
        _bind_mousewheel(self.rows_frame)

    def _clear(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self._editing_code = None
        if hasattr(self, "save_edit_btn"):
            self.save_edit_btn.pack_forget()

    def _fill_form(self, values):
        self._clear()
        for field, val in zip(COLLEGE_FIELDS, values):
            self.entries[field].insert(0, val)
        self._editing_code = values[0]  # first field is always "code"
        self.save_edit_btn.pack(side="left", padx=4)
        self.save_edit_btn.lift()

    def refresh(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        for row_idx, c in enumerate(load_data(COLLEGE_FILE)):
            bg = "#f0f0f0" if row_idx % 2 == 0 else "#ffffff"
            values = [c.get(f, "") for f in COLLEGE_FIELDS]

            for col_idx, (val, w) in enumerate(zip(values, COL_WIDTHS)):
                lbl = tk.Label(self.rows_frame, text=val, bg=bg,
                               width=w // 7, anchor="w")
                lbl.grid(row=row_idx, column=col_idx, padx=4, pady=2, sticky="w")
                self._bind_mousewheel(lbl)

            af = tk.Frame(self.rows_frame, bg=bg)
            af.grid(row=row_idx, column=len(COLLEGE_FIELDS), padx=4, pady=2)
            self._bind_mousewheel(af)
            tk.Button(af, text="Edit",   width=5, bg="#4a90d9", fg="white",
                      command=lambda v=values: self._fill_form(v)).pack(side="left", padx=2)
            tk.Button(af, text="Delete", width=6, bg="#d9534f", fg="white",
                      command=lambda code=c["code"]: self._delete(code)).pack(side="left", padx=2)

    def add(self):
        data = {f: self.entries[f].get().strip() for f in COLLEGE_FIELDS}
        colleges = load_data(COLLEGE_FILE)
        if any(c["code"] == data["code"] for c in colleges):
            messagebox.showerror("Error", "College code already exists.")
            return
        colleges.append(data)
        save_data(COLLEGE_FILE, COLLEGE_FIELDS, colleges)
        self.refresh()
        self._clear()

    def _commit_edit(self):
        if not self._editing_code:
            messagebox.showerror("Error", "No college selected for editing.")
            return
        data = {f: self.entries[f].get().strip() for f in COLLEGE_FIELDS}
        colleges = load_data(COLLEGE_FILE)
        # If the code changed, ensure it doesn't clash with another record
        if data["code"] != self._editing_code:
            if any(c["code"] == data["code"] for c in colleges):
                messagebox.showerror("Error", "College code already exists.")
                return
            # Cascade the code change to all programs that reference it
            from config import PROGRAM_FIELDS
            programs = load_data(PROGRAM_FILE)
            for p in programs:
                if p.get("college_code") == self._editing_code:
                    p["college_code"] = data["code"]
            save_data(PROGRAM_FILE, PROGRAM_FIELDS, programs)
        # Replace the matching record in place
        colleges = [data if c["code"] == self._editing_code else c for c in colleges]
        save_data(COLLEGE_FILE, COLLEGE_FIELDS, colleges)
        self.refresh()
        self._clear()

    def _delete(self, code):
        if any(p["college_code"] == code for p in load_data(PROGRAM_FILE)):
            messagebox.showerror("Error", "Cannot delete. College has programs.")
            return
        if not messagebox.askyesno("Confirm", f"Delete college {code}?"):
            return
        colleges = [c for c in load_data(COLLEGE_FILE) if c["code"] != code]
        save_data(COLLEGE_FILE, COLLEGE_FIELDS, colleges)
        self.refresh()
