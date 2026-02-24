# ---------------- FILE CONFIG ---------------- #

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STUDENT_FILE = os.path.join(_BASE_DIR, "students.csv")
PROGRAM_FILE = os.path.join(_BASE_DIR, "programs.csv")
COLLEGE_FILE = os.path.join(_BASE_DIR, "colleges.csv")

STUDENT_FIELDS = ["id", "firstname", "lastname", "program_code", "year", "gender"]
PROGRAM_FIELDS = ["code", "name", "college_code"]
COLLEGE_FIELDS = ["code", "name"]
