
from __future__ import annotations
import csv, os
from .gradebook import Gradebook

def export_student_csv(gb: Gradebook, student_id: str, out_path: str) -> str:
    st = gb.get_student(student_id)
    fields = ["student_id","name","assignment_id","assignment_name","score","max_points","weight","percent"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fields)
        for aid, a in gb.assignments.items():
            score = gb.grades.get(student_id, {}).get(aid, 0.0)
            pct = (score / a.max_points) * 100.0 if a.max_points else 0.0
            w.writerow([st.student_id, f"{st.first_name} {st.last_name}", aid, a.name,
                        f"{score:.2f}", f"{a.max_points:.2f}", f"{a.weight:.3f}", f"{pct:.2f}"])
        w.writerow([]); w.writerow(["Final %", f"{gb.student_percentage(student_id):.2f}"])
        w.writerow(["GPA", f"{gb.student_gpa(student_id):.2f}"])
    return out_path

def export_all_students_csv(gb: Gradebook, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    for sid in gb.students:
        export_student_csv(gb, sid, os.path.join(folder, f"{sid}_report.csv"))
    return folder

def export_student_pdf(gb: Gradebook, student_id: str, out_path: str) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except Exception as e:
        raise RuntimeError("PDF export requires reportlab. Install with 'pip install reportlab'.") from e
    st = gb.get_student(student_id); os.makedirs(os.path.dirname(out_path), exist_ok=True)
    c = canvas.Canvas(out_path, pagesize=A4); W,H=A4; y=H-2*cm
    c.setFont("Helvetica-Bold", 16); c.drawString(2*cm, y, "Student Grade Report"); y-=1*cm
    c.setFont("Helvetica", 12); c.drawString(2*cm, y, f"Name: {st.first_name} {st.last_name} (ID: {st.student_id})"); y-=0.5*cm
    c.drawString(2*cm, y, f"Final %: {gb.student_percentage(student_id):.2f}   GPA: {gb.student_gpa(student_id):.2f}"); y-=1*cm
    c.setFont("Helvetica-Bold", 12); c.drawString(2*cm, y, "Assignments:"); y-=0.6*cm; c.setFont("Helvetica", 11)
    for aid, a in gb.assignments.items():
        score = gb.grades.get(student_id, {}).get(aid, 0.0); pct=(score/a.max_points)*100.0 if a.max_points else 0.0
        line = f"{a.name} [{a.type}]  score: {score:.2f}/{a.max_points:.2f}  weight: {a.weight:.2f}  pct: {pct:.1f}%"
        c.drawString(2*cm, y, line); y-=0.5*cm
        if y<2*cm: c.showPage(); y=H-2*cm; c.setFont("Helvetica", 11)
    c.showPage(); c.save(); return out_path
