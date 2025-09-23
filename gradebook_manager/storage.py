
from __future__ import annotations
import csv, os
from typing import Iterable
from .models import Student, Assignment

def load_students_csv(path: str) -> Iterable[Student]:
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            yield Student(
                student_id=row["student_id"],
                first_name=row.get("first_name",""),
                last_name=row.get("last_name",""),
                email=row.get("email",""),
            )

def load_assignments_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            yield Assignment(
                assignment_id=row["assignment_id"],
                name=row["name"],
                max_points=float(row.get("max_points",100.0)),
                weight=float(row.get("weight",0.0)),
                type=row.get("type","generic"),
            )

def load_grades_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            yield (row["student_id"], row["assignment_id"], float(row["score"]))

def load_passwords_csv(path: str):
    import csv, os
    mapping = {}
    if not os.path.exists(path):
        return mapping
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            role = (row.get("role") or "").strip().lower()
            username = (row.get("username") or "").strip()
            password = row.get("password") or ""
            if role and username:
                mapping[(role, username)] = password
    return mapping

def save_passwords_csv(path: str, mapping):
    import csv, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["role","username","password"])
        for (role, username), password in mapping.items():
            w.writerow([role, username, password])

def save_students_csv(path: str, students: dict):
    import csv, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id","first_name","last_name","email"])
        for s in students.values():
            w.writerow([s.student_id, s.first_name, s.last_name, s.email])

def save_assignments_csv(path: str, assignments: dict):
    import csv, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["assignment_id","name","max_points","weight","type"])
        for a in assignments.values():
            w.writerow([a.assignment_id, a.name, f"{a.max_points:.6g}", f"{a.weight:.6g}", a.type])

def save_grades_csv(path: str, grades: dict):
    import csv, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id","assignment_id","score"])
        for sid, gdict in grades.items():
            for aid, score in gdict.items():
                w.writerow([sid, aid, f"{float(score):.6g}"])


