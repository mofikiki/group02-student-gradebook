
from __future__ import annotations
import argparse, os, tkinter as tk
from .gradebook import Gradebook
from .storage import load_students_csv, load_assignments_csv, load_grades_csv
from .reports import export_all_students_csv
from .ui import GradebookApp
from .auth import login_flow

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_sample_data(gb: Gradebook):
    # Sample seed
    students_p = os.path.join(DATA_DIR, "sample_students.csv")
    assignments_p = os.path.join(DATA_DIR, "sample_assignments.csv")
    grades_p = os.path.join(DATA_DIR, "sample_grades.csv")

    # Persisted files (autosave writes these)
    students_live = os.path.join(DATA_DIR, "students.csv")
    assignments_live = os.path.join(DATA_DIR, "assignments.csv")
    grades_live = os.path.join(DATA_DIR, "grades.csv")

    def _merge_students(path):
        if os.path.exists(path):
            for st in load_students_csv(path):
                try: gb.add_student(st)
                except Exception: pass

    def _merge_assignments(path):
        if os.path.exists(path):
            for a in load_assignments_csv(path):
                try: gb.add_assignment(a)
                except Exception: pass

    def _merge_grades(path):
        if os.path.exists(path):
            for sid, aid, score in load_grades_csv(path):
                try: gb.enter_grade(sid, aid, score)
                except Exception: pass

    # Load samples first, then live files (live overwrites/extends)
    _merge_students(students_p); _merge_assignments(assignments_p); _merge_grades(grades_p)
    _merge_students(students_live); _merge_assignments(assignments_live); _merge_grades(grades_live)

def main():
    ap = argparse.ArgumentParser(description="Student Gradebook Manager")
    ap.add_argument("--export-all-csv", action="store_true", help="Export CSV reports for all students and exit")
    ap.add_argument("--strict-weights", action="store_true", help="Require weights to sum to 1.0 (no normalization)")
    args = ap.parse_args()

    gb = Gradebook(strict_weights=args.strict_weights)
    load_sample_data(gb)

    if args.export_all_csv:
        out_dir = os.path.join(os.getcwd(), "reports_csv")
        export_all_students_csv(gb, out_dir)
        print(f"CSV reports exported to: {out_dir}")
        return

    root = tk.Tk(); root.withdraw()
    session = login_flow(root, gb, DATA_DIR)
    if not session: return
    app = GradebookApp(gb, data_dir=DATA_DIR, session=session)
    root.destroy(); app.mainloop()

if __name__ == "__main__":
    main()
