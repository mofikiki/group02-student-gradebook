
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, re
from .gradebook import Gradebook
from .models import Student, Assignment
from .reports import export_student_csv, export_student_pdf
from .exceptions import GradebookError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

class GradebookApp(tk.Tk):
    def __init__(self, gb: Gradebook, data_dir: str, session: dict):
        super().__init__()
        self.title("Student Gradebook Manager")
        self.geometry("980x640")
        self.gb = gb
        self.data_dir = data_dir
        self.session = session
        self.role = tk.StringVar(value=("Teacher" if session.get("role") == "Teacher" else "Viewer"))

        self._setup_style()
        self._build_menu()
        self._build_layout()
        self._refresh_views()

    # ---------- Styling ----------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        BG="#0f172a"; PANEL="#111827"; FG="#e5e7eb"; MUTED="#9ca3af"; ACC="#2563eb"; ACC2="#1d4ed8"; GRID="#334155"
        self.configure(bg=BG)
        style.configure(".", background=BG, foreground=FG)
        style.configure("TFrame", background=BG)
        style.configure("TLabelframe", background=BG, foreground=FG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TButton", background=ACC, foreground="white", padding=6, relief="flat")
        style.map("TButton", background=[("active", ACC2), ("pressed", "#1e40af"), ("disabled", GRID)],
                              foreground=[("disabled", MUTED)])
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=FG, arrowcolor=FG, bordercolor=GRID)
        style.configure("TEntry", fieldbackground=PANEL, foreground=FG)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG, bordercolor=GRID, rowheight=22)
        style.configure("Treeview.Heading", background="#1f2937", foreground=FG)
        style.map("Treeview.Heading", background=[("active", "#374151")])

    # ---------- Menus ----------
    def _build_menu(self):
        m = tk.Menu(self)

        filem = tk.Menu(m, tearoff=0)
        if self.session.get("role") == "Teacher":
            filem.add_command(label="Import Roster (CSV)...", command=self._import_roster)
            filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy)
        m.add_cascade(label="File", menu=filem)

        if self.session.get("role") == "Teacher":
            toolsm = tk.Menu(m, tearoff=0)
            toolsm.add_command(label="Curve +5 points", command=lambda: self._apply_curve(kind="add", value=5))
            toolsm.add_command(label="Scale x1.05", command=lambda: self._apply_curve(kind="scale", value=1.05))
            m.add_cascade(label="Tools", menu=toolsm)

        accountm = tk.Menu(m, tearoff=0)
        from .auth import change_password_dialog
        if self.session.get("role") == "Student":
            accountm.add_command(label="Change Password...", command=lambda: change_password_dialog(self, self.data_dir, "Student", self.session.get("student_id")))
            accountm.add_separator()
        elif self.session.get("role") == "Teacher":
            accountm.add_command(label="Change Password...", command=lambda: change_password_dialog(self, self.data_dir, "Teacher", self.session.get("username")))
            accountm.add_separator()
        accountm.add_command(label="Log Out / Switch User...", command=self._logout)
        m.add_cascade(label="Account", menu=accountm)

        helpm = tk.Menu(m, tearoff=0)
        helpm.add_command(label="About", command=lambda: messagebox.showinfo("About", "Student Gradebook Manager"))
        m.add_cascade(label="Help", menu=helpm)

        self.config(menu=m)

    # ---------- Layout ----------
    def _build_layout(self):
        # Top bar: signed-in + class average
        top = ttk.Frame(self, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)
        self.signed_in_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.signed_in_var).pack(side=tk.LEFT, padx=(0,20))
        self.class_avg_var = tk.StringVar(value="Class Avg: 0.00%")
        ttk.Label(top, textvariable=self.class_avg_var, font=("TkDefaultFont", 11, "bold")).pack(side=tk.LEFT)

        # Main panes
        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left pane: students
        left = ttk.Frame(main, padding=6)
        self.students_tv = ttk.Treeview(left, columns=("id","first","last","email"), show="headings", height=10)
        for c in ("id","first","last","email"):
            self.students_tv.heading(c, text=c.title())
            self.students_tv.column(c, width=140 if c=="email" else 100, stretch=True)
        self.students_tv.pack(fill=tk.BOTH, expand=True)

        st_form = ttk.LabelFrame(left, text="Add / Update Student", padding=8)
        self.st_id = tk.Entry(st_form, width=12)
        self.st_first = tk.Entry(st_form, width=16)
        self.st_last = tk.Entry(st_form, width=16)
        self.st_email = tk.Entry(st_form, width=20)
        _grid4(st_form, ["ID","First","Last","Email"], [self.st_id,self.st_first,self.st_last,self.st_email])
        btns = ttk.Frame(st_form)
        self.btn_add_student = ttk.Button(btns, text="Add", command=self._add_student); self.btn_add_student.pack(side=tk.LEFT, padx=4)
        self.btn_del_student = ttk.Button(btns, text="Delete", command=self._del_student); self.btn_del_student.pack(side=tk.LEFT, padx=4)
        self.btn_export_csv = ttk.Button(btns, text="Export CSV", command=self._export_selected_csv); self.btn_export_csv.pack(side=tk.LEFT, padx=4)
        self.btn_export_pdf = ttk.Button(btns, text="Export PDF", command=self._export_selected_pdf); self.btn_export_pdf.pack(side=tk.LEFT, padx=4)
        btns.grid(row=2, column=0, columnspan=4, pady=(6,0))
        st_form.pack(fill=tk.X, pady=6)

        main.add(left, weight=1)

        # Right: assignments + grades + summary
        right = ttk.Frame(main, padding=6)
        self.assign_tv = ttk.Treeview(right, columns=("id","name","max","weight","type"), show="headings", height=10)
        for c,w in (("id",90),("name",140),("max",80),("weight",80),("type",90)):
            self.assign_tv.heading(c, text=c.title()); self.assign_tv.column(c, width=w, stretch=True)
        self.assign_tv.pack(fill=tk.BOTH, expand=True)

        as_form = ttk.LabelFrame(right, text="Add Assignment", padding=8)
        self.as_id = tk.Entry(as_form, width=12)
        self.as_name = tk.Entry(as_form, width=18)
        self.as_max = tk.Entry(as_form, width=8)
        self.as_weight = tk.Entry(as_form, width=8)
        self.as_type = ttk.Combobox(as_form, values=["quiz","exam","project","homework","generic"], width=10, state="readonly")
        self.as_type.set("generic")
        _grid5(as_form, ["ID","Name","Max","Weight","Type"], [self.as_id,self.as_name,self.as_max,self.as_weight,self.as_type])
        self.btn_add_assignment = ttk.Button(as_form, text="Add", command=self._add_assignment)
        self.btn_add_assignment.grid(row=2, column=0, columnspan=5, pady=(6,0))
        as_form.pack(fill=tk.X, pady=6)

        grade_form = ttk.LabelFrame(right, text="Enter Grade", padding=8)
        self.grade_sid = tk.Entry(grade_form, width=12)
        self.grade_aid = tk.Entry(grade_form, width=12)
        self.grade_score = tk.Entry(grade_form, width=10)
        _grid3(grade_form, ["Student ID","Assignment ID","Score"], [self.grade_sid,self.grade_aid,self.grade_score])
        self.btn_save_grade = ttk.Button(grade_form, text="Save Grade", command=self._save_grade)
        self.btn_save_grade.grid(row=2, column=0, columnspan=3, pady=(6,0))
        grade_form.pack(fill=tk.X, pady=6)

        summary = ttk.LabelFrame(right, text="Summary (Selected Student)", padding=8)
        self.summary_text = tk.Text(summary, height=6, width=60)
        self.summary_text.configure(bg="#111827", fg="#e5e7eb", insertbackground="#e5e7eb")
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        summary.pack(fill=tk.BOTH, expand=True, pady=(4,0))

        main.add(right, weight=1)

        self.students_tv.bind("<<TreeviewSelect>>", lambda e: self._update_summary())
        self._toggle_role()

    # ---------- Role gating ----------
    def _toggle_role(self):
        viewer = (self.session.get("role") == "Student")
        # entries
        for w in [self.st_id, self.st_first, self.st_last, self.st_email]:
            w.config(state="disabled" if viewer else "normal")
        for w in [self.as_id, self.as_name, self.as_max, self.as_weight, self.as_type,
                  self.grade_sid, self.grade_aid, self.grade_score]:
            if isinstance(w, ttk.Combobox):
                w.config(state="disabled" if viewer else "readonly")
            else:
                w.config(state="disabled" if viewer else "normal")
        # buttons
        for b in [getattr(self,'btn_add_student',None), getattr(self,'btn_del_student',None),
                  getattr(self,'btn_add_assignment',None), getattr(self,'btn_save_grade',None)]:
            if b is not None:
                b.config(state=("disabled" if viewer else "normal"))

    def _logout(self):
        """Log out and return to login; rebuild UI with new session or exit on cancel."""
        from .auth import login_flow
        self.withdraw()
        session = login_flow(self, self.gb, self.data_dir)
        if not session:
            self.destroy()
            return
        self.session = session
        self.role.set("Teacher" if session.get("role") == "Teacher" else "Viewer")
        self._build_menu()
        self._refresh_views()
        self._toggle_role()
        self.deiconify()

    # ---------- Persistence ----------
    def _save_all_to_csv(self):
        from .storage import save_students_csv, save_assignments_csv, save_grades_csv
        save_students_csv(os.path.join(self.data_dir, "students.csv"), self.gb.students)
        save_assignments_csv(os.path.join(self.data_dir, "assignments.csv"), self.gb.assignments)
        save_grades_csv(os.path.join(self.data_dir, "grades.csv"), self.gb.grades)

    # ---------- Refresh ----------
    def _refresh_views(self):
        # students
        for i in self.students_tv.get_children():
            self.students_tv.delete(i)
        if self.session.get("role") == "Student":
            sid = self.session.get("student_id")
            s = self.gb.get_student(sid)
            self.students_tv.insert("", tk.END, iid=s.student_id, values=(s.student_id, s.first_name, s.last_name, s.email))
            self.students_tv.selection_set(s.student_id)
            self.students_tv.focus(s.student_id)
        else:
            for s in self.gb.students.values():
                self.students_tv.insert("", tk.END, iid=s.student_id, values=(s.student_id, s.first_name, s.last_name, s.email))

        # assignments
        for i in self.assign_tv.get_children():
            self.assign_tv.delete(i)
        for a in self.gb.assignments.values():
            self.assign_tv.insert("", tk.END, iid=a.assignment_id, values=(a.assignment_id, a.name, a.max_points, a.weight, a.type))

        # top labels
        self.class_avg_var.set(f"Class Avg: {self.gb.class_average():.2f}%")
        if self.session.get("role") == "Teacher":
            self.signed_in_var.set("Signed in: Teacher")
        else:
            self.signed_in_var.set(f"Signed in: Student {self.session.get('student_id')}")

        self._update_summary()

    # ---------- Actions ----------
    def _add_student(self):
        try:
            sid = self.st_id.get().strip()
            first = self.st_first.get().strip()
            last  = self.st_last.get().strip()
            email = self.st_email.get().strip()

            if not sid:
                messagebox.showerror("Error", "Student ID is required.")
                return
            if email and not EMAIL_RE.match(email):
                messagebox.showerror("Error", "Please enter a valid email address.")
                return

            st = Student(sid, first, last, email)
            self.gb.add_student(st)
            self._refresh_views()
            self._save_all_to_csv()

            self.st_id.delete(0, tk.END); self.st_first.delete(0, tk.END)
            self.st_last.delete(0, tk.END); self.st_email.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _del_student(self):
        sel = self.students_tv.selection()
        if not sel:
            messagebox.showwarning("Delete", "Select a student first.")
            return
        sid = sel[0]
        if not messagebox.askyesno("Delete Student", f"Remove {sid}? This also deletes the student's grades."):
            return
        try:
            self.gb.delete_student(sid)
            self._refresh_views()
            self._save_all_to_csv()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_assignment(self):
        try:
            a = Assignment(assignment_id=self.as_id.get().strip(), name=self.as_name.get().strip(),
                           max_points=float(self.as_max.get().strip() or 100.0),
                           weight=float(self.as_weight.get().strip() or 0.0),
                           type=self.as_type.get().strip() or "generic")
            self.gb.add_assignment(a)
            self._refresh_views()
            self._save_all_to_csv()
            for w in [self.as_id, self.as_name, self.as_max, self.as_weight]: w.delete(0, tk.END)
            self.as_type.set("generic")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_grade(self):
        try:
            sid = self.grade_sid.get().strip(); aid = self.grade_aid.get().strip(); score = float(self.grade_score.get().strip())
            self.gb.enter_grade(sid, aid, score)
            self._refresh_views()
            self._save_all_to_csv()
            for w in [self.grade_sid, self.grade_aid, self.grade_score]: w.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_summary(self):
        sel = self.students_tv.selection()
        if not sel:
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, "Select a student to see summary...\n")
            return
        sid = sel[0]; st = self.gb.get_student(sid)
        lines = [f"Student: {st.first_name} {st.last_name} ({st.student_id})",
                 f"Final %: {self.gb.student_percentage(sid):.2f}",
                 f"GPA: {self.gb.student_gpa(sid):.2f}",
                 "Assignments:"]
        for aid, a in self.gb.assignments.items():
            score = self.gb.grades.get(sid, {}).get(aid, 0.0)
            lines.append(f" - {a.name} [{a.type}] {score:.2f}/{a.max_points:.2f} (w={a.weight:.2f})")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(lines))

    def _export_selected_csv(self):
        sel = self.students_tv.selection()
        if not sel: return
        sid = sel[0]
        path = filedialog.asksaveasfilename(title="Save CSV", defaultextension=".csv", filetypes=[("CSV","*.csv")], initialfile=f"{sid}_report.csv")
        if not path: return
        export_student_csv(self.gb, sid, path)
        messagebox.showinfo("Export", f"Saved: {path}")

    def _export_selected_pdf(self):
        sel = self.students_tv.selection()
        if not sel: return
        sid = sel[0]
        path = filedialog.asksaveasfilename(title="Save PDF", defaultextension=".pdf", filetypes=[("PDF","*.pdf")], initialfile=f"{sid}_report.pdf")
        if not path: return
        try:
            export_student_pdf(self.gb, sid, path)
            messagebox.showinfo("Export", f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Export", str(e))

    def _import_roster(self):
        path = filedialog.askopenfilename(title="Import Roster CSV", filetypes=[("CSV","*.csv")])
        if not path: return
        import csv
        added = 0
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                sid = row.get("student_id","").strip()
                if not sid: continue
                try:
                    self.gb.add_student(Student(sid, row.get("first_name",""), row.get("last_name",""), row.get("email",""))); added += 1
                except Exception:
                    pass
        messagebox.showinfo("Import", f"Imported {added} students")
        self._refresh_views()

    def _apply_curve(self, kind: str, value: float):
        if kind == "add":
            self.gb.curve_add(float(value))
        else:
            self.gb.curve_scale(float(value))
        self._refresh_views()

def _grid4(frame, labels, widgets):
    for i,(lab,w) in enumerate(zip(labels, widgets)):
        ttk.Label(frame, text=lab).grid(row=0, column=i, sticky="w", padx=3, pady=2)
        w.grid(row=1, column=i, sticky="we", padx=3, pady=2)

def _grid5(frame, labels, widgets):
    for i,(lab,w) in enumerate(zip(labels, widgets)):
        ttk.Label(frame, text=lab).grid(row=0, column=i, sticky="w", padx=3, pady=2)
        w.grid(row=1, column=i, sticky="we", padx=3, pady=2)

def _grid3(frame, labels, widgets):
    for i,(lab,w) in enumerate(zip(labels, widgets)):
        ttk.Label(frame, text=lab).grid(row=0, column=i, sticky="w", padx=3, pady=2)
        w.grid(row=1, column=i, sticky="we", padx=3, pady=2)
