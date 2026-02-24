import csv
import os
import re


def ensure_file(filename, headers):
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def load_data(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_data(filename, fieldnames, data):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def valid_student_id(sid):
    return re.match(r"^\d{4}-\d{4}$", sid)
