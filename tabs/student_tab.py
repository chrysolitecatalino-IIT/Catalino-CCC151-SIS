import tkinter as tk
from tkinter import ttk, messagebox

from config import STUDENT_FILE, STUDENT_FIELDS, PROGRAM_FILE
from utils import load_data, save_data, valid_student_id


COL_WIDTHS = [90, 110, 110, 100, 50, 70]
LABELS     = ["ID", "First Name", "Last Name", "Program", "Year", "Gender"]
PAGE_SIZE  = 50


class StudentTab:

    def __init__(self, notebook):
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Students")
        self._current_page = 0
        self._all_students = []
        self._build_ui()
        self.tab.after(100, self.refresh)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # form
        form = tk.LabelFrame(self.tab, text="Student Details", padx=8, pady=8)
        form.pack(fill="x", padx=10, pady=(10, 0))

        field_labels = ["ID (YYYY-NNNN)", "First Name", "Last Name",
                        "Program Code", "Year", "Gender"]
        self.entries = {}
        for i, label in enumerate(field_labels):
            tk.Label(form, text=label).grid(row=i // 3, column=(i % 3) * 2,
                                            padx=6, pady=4, sticky="e")
            entry = tk.Entry(form, width=18)
            entry.grid(row=i // 3, column=(i % 3) * 2 + 1, padx=6, sticky="w")
            self.entries[STUDENT_FIELDS[i]] = entry

        btn_frame = tk.Frame(self.tab)
        btn_frame.pack(pady=6)
        self.save_edit_btn = tk.Button(btn_frame, text="Save Edit", width=9,
                                       command=self._commit_edit,
                                       bg="#5cb85c", fg="white")
        # not packed yet — only shown when editing
        tk.Button(btn_frame, text="Add",   width=9, command=self.add).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Clear", width=9, command=self._clear).pack(side="left", padx=4)
        self._editing_id = None

        # search bar
        sf = tk.Frame(self.tab)
        sf.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(sf, text="Search ID:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())
        tk.Entry(sf, textvariable=self.search_var, width=20).pack(side="left", padx=4)

        # table header
        header = tk.Frame(self.tab, bg="#3c3f41")
        header.pack(fill="x", padx=10)
        for i, (lbl, w) in enumerate(zip(LABELS, COL_WIDTHS)):
            tk.Label(header, text=lbl, bg="#3c3f41", fg="white",
                     width=w // 7, anchor="w").grid(row=0, column=i, padx=4, pady=3)
        tk.Label(header, text="Actions", bg="#3c3f41", fg="white",
                 width=14, anchor="w").grid(row=0, column=len(LABELS), padx=4)

        # scrollable rows
        container = tk.Frame(self.tab)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 0))

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._canvas = canvas

        self.rows_frame = tk.Frame(canvas)
        self.canvas_window = canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")

        self.rows_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.canvas_window, width=e.width))

        def _on_mousewheel(event):
            # Windows/macOS use delta; Linux uses Button-4/5
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

        # pagination controls
        pg = tk.Frame(self.tab)
        pg.pack(fill="x", padx=10, pady=(2, 8))
        tk.Button(pg, text="◀ Prev", width=8, command=self._prev_page).pack(side="left", padx=2)
        tk.Button(pg, text="Next ▶", width=8, command=self._next_page).pack(side="left", padx=2)
        self.page_label = tk.Label(pg, text="Page 1")
        self.page_label.pack(side="left", padx=8)
        self.count_label = tk.Label(pg, text="")
        self.count_label.pack(side="left", padx=8)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _clear(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self._editing_id = None
        if hasattr(self, "save_edit_btn"):
            self.save_edit_btn.pack_forget()

    def _fill_form(self, values):
        self._clear()
        for field, val in zip(STUDENT_FIELDS, values):
            self.entries[field].insert(0, val)
        self._editing_id = values[0]  # first field is always "id"
        self.save_edit_btn.pack(side="left", padx=4)
        self.save_edit_btn.lift()
            
    def _on_search(self):
        if not hasattr(self, "rows_frame"):
            return
        self._current_page = 0
        self.refresh()

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        total_pages = max(1, (len(self._all_students) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_page()

    # ── refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        if not hasattr(self, "rows_frame"):
            return

        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        students = load_data(STUDENT_FILE)
        if query:
            students = [s for s in students if query in s.get("id", "").lower()]

        self._all_students = students
        self._render_page()

    def _render_page(self):
        # clear existing rows
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        students = self._all_students
        total = len(students)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

        # clamp page
        if self._current_page >= total_pages:
            self._current_page = total_pages - 1

        start = self._current_page * PAGE_SIZE
        end   = min(start + PAGE_SIZE, total)
        page_students = students[start:end]

        for row_idx, s in enumerate(page_students):
            bg = "#f0f0f0" if row_idx % 2 == 0 else "#ffffff"
            values = [s.get(f, "") for f in STUDENT_FIELDS]

            for col_idx, (val, w) in enumerate(zip(values, COL_WIDTHS)):
                lbl = tk.Label(self.rows_frame, text=val, bg=bg,
                               width=w // 7, anchor="w")
                lbl.grid(row=row_idx, column=col_idx, padx=4, pady=2, sticky="w")
                self._bind_mousewheel(lbl)

            af = tk.Frame(self.rows_frame, bg=bg)
            af.grid(row=row_idx, column=len(STUDENT_FIELDS), padx=4, pady=2)
            self._bind_mousewheel(af)
            tk.Button(af, text="Edit",   width=5, bg="#4a90d9", fg="white",
                      command=lambda v=values: self._fill_form(v)).pack(side="left", padx=2)
            tk.Button(af, text="Delete", width=6, bg="#d9534f", fg="white",
                      command=lambda sid=s["id"]: self._delete(sid)).pack(side="left", padx=2)

        # scroll back to top on page change
        self._canvas.yview_moveto(0)

        # update pagination labels
        self.page_label.config(text=f"Page {self._current_page + 1} of {total_pages}")
        self.count_label.config(text=f"({total} students)")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add(self):
        data = {f: self.entries[f].get().strip() for f in STUDENT_FIELDS}
        if not valid_student_id(data["id"]):
            messagebox.showerror("Error", "Invalid ID format (YYYY-NNNN).")
            return
        if not data["firstname"] or not data["lastname"]:
            messagebox.showerror("Error", "First and last name cannot be empty.")
            return
        if not any(p["code"] == data["program_code"] for p in load_data(PROGRAM_FILE)):
            messagebox.showerror("Error", "Program does not exist.")
            return
        if not data["year"].isdigit() or not (1 <= int(data["year"]) <= 5):
            messagebox.showerror("Error", "Year must be a number between 1 and 5.")
            return
        if not data["gender"]:
            messagebox.showerror("Error", "Gender cannot be empty.")
            return
        students = load_data(STUDENT_FILE)
        if any(s["id"] == data["id"] for s in students):
            messagebox.showerror("Error", "Student ID already exists.")
            return
        students.append(data)
        save_data(STUDENT_FILE, STUDENT_FIELDS, students)
        self.refresh()
        self._clear()

    def _commit_edit(self):
        if not self._editing_id:
            messagebox.showerror("Error", "No student selected for editing.")
            return
        data = {f: self.entries[f].get().strip() for f in STUDENT_FIELDS}
        if not data["firstname"] or not data["lastname"]:
            messagebox.showerror("Error", "First and last name cannot be empty.")
            return
        if not any(p["code"] == data["program_code"] for p in load_data(PROGRAM_FILE)):
            messagebox.showerror("Error", "Program does not exist.")
            return
        if not data["year"].isdigit() or not (1 <= int(data["year"]) <= 5):
            messagebox.showerror("Error", "Year must be a number between 1 and 5.")
            return
        if not data["gender"]:
            messagebox.showerror("Error", "Gender cannot be empty.")
            return
        students = load_data(STUDENT_FILE)
        for s in students:
            if s["id"] == self._editing_id:
                for f in STUDENT_FIELDS:
                    if f != "id":
                        s[f] = data[f]
                save_data(STUDENT_FILE, STUDENT_FIELDS, students)
                self.refresh()
                self._clear()
                return
        messagebox.showerror("Error", "Student not found.")

    def _save_edit(self, data, win):
        pass  # superseded by _commit_edit

    def _delete(self, sid):
        if not messagebox.askyesno("Confirm", f"Delete student {sid}?"):
            return
        students = [s for s in load_data(STUDENT_FILE) if s["id"] != sid]
        save_data(STUDENT_FILE, STUDENT_FIELDS, students)
        self.refresh()
        self._clear()
