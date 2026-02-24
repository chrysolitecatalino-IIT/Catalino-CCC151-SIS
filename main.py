import tkinter as tk
from tkinter import ttk

from config import STUDENT_FILE, STUDENT_FIELDS, PROGRAM_FILE, PROGRAM_FIELDS, COLLEGE_FILE, COLLEGE_FIELDS
from utils import ensure_file
from tabs import StudentTab, ProgramTab, CollegeTab


class SISApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Student Information System")
        self.root.geometry("1000x600")

        ensure_file(STUDENT_FILE, STUDENT_FIELDS)
        ensure_file(PROGRAM_FILE, PROGRAM_FIELDS)
        ensure_file(COLLEGE_FILE, COLLEGE_FIELDS)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        StudentTab(self.notebook)
        ProgramTab(self.notebook)
        CollegeTab(self.notebook)


if __name__ == "__main__":
    root = tk.Tk()
    app = SISApp(root)
    root.mainloop()
