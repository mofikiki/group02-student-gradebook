
from __future__ import annotations
import os, tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple
from .storage import load_passwords_csv, save_passwords_csv

class _Palette:
    BG="#0f172a"; PANEL="#111827"; FG="#e5e7eb"; MUTED="#9ca3af"; ACC="#2563eb"; ACC2="#1d4ed8"; GRID="#334155"

def _apply_style(win):
    style = ttk.Style(win)
    try: style.theme_use("clam")
    except Exception: pass
    p=_Palette
    win.configure(bg=p.BG)
    style.configure(".", background=p.BG, foreground=p.FG)
    style.configure("TFrame", background=p.BG)
    style.configure("TLabelframe", background=p.BG, foreground=p.FG)
    style.configure("TLabelframe.Label", background=p.BG, foreground=p.FG)
    style.configure("TLabel", background=p.BG, foreground=p.FG)
    style.configure("TButton", background=p.ACC, foreground="white", padding=6, relief="flat")
    style.map("TButton", background=[("active", p.ACC2), ("pressed","#1e40af"), ("disabled", p.GRID)], foreground=[("disabled", p.MUTED)])
    style.configure("TEntry", fieldbackground=p.PANEL, foreground=p.FG)
    style.configure("TCombobox", fieldbackground=p.PANEL, background=p.PANEL, foreground=p.FG, arrowcolor=p.FG, bordercolor=p.GRID)

def ensure_default_passwords(gb, passwords: Dict[Tuple[str, str], str], data_dir: str):
    if ("teacher","teacher") not in passwords: passwords[("teacher","teacher")] = "teacher"
    for s in gb.students.values():
        key=("student", s.student_id)
        if key not in passwords: passwords[key] = (s.first_name or "").strip()
    save_passwords_csv(os.path.join(data_dir, "passwords.csv"), passwords)

class LoginDialog(tk.Toplevel):
    def __init__(self, master, gb, data_dir: str):
        super().__init__(master)
        self.title("Sign In")
        self.geometry("360x260"); self.resizable(False, False)
        _apply_style(self)
        self.result=None; self.data_dir=data_dir; self.gb=gb

        self.passwords = load_passwords_csv(os.path.join(data_dir, "passwords.csv"))
        ensure_default_passwords(gb, self.passwords, data_dir)

        header = tk.Frame(self, height=36, bg=_Palette.ACC); header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="Login", bg=_Palette.ACC, fg="white", font=("TkDefaultFont", 12, "bold")).pack(side=tk.LEFT, padx=12, pady=6)

        labf = ttk.LabelFrame(self, text="Login", padding=10)
        self.geometry("360x260")  # a little taller so everything fits

        labf = ttk.LabelFrame(self, text="Login", padding=10)
        labf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        labf.columnconfigure(0, weight=0)
        labf.columnconfigure(1, weight=1)

        # Make column 1 stretch so entries/combobox render fully
        labf.columnconfigure(0, weight=0)
        labf.columnconfigure(1, weight=1)

        row=0
        ttk.Label(labf, text="Role").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.role=tk.StringVar(value="Teacher")
        ttk.Combobox(labf, textvariable=self.role, values=["Teacher","Student"], state="readonly", width=16)            .grid(row=row, column=1, sticky="w", padx=5, pady=5)

        row+=1
        ttk.Label(labf, text="Username").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.username=tk.Entry(labf, width=20); self.username.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.username.insert(0,"teacher")

        row+=1
        ttk.Label(labf, text="Password").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.password=tk.Entry(labf, show="•", width=20); self.password.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.password.insert(0,"teacher")

        row+=1
        btns = ttk.Frame(labf); btns.grid(row=row, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Sign In", command=self._do_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side=tk.LEFT, padx=5)

        self.grab_set(); self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _cancel(self): self.result=None; self.destroy()

    def _do_login(self):
        role=self.role.get(); uname=(self.username.get() or "").strip(); pw=self.password.get() or ""
        if role=="Teacher":
            key=("teacher", uname)
            if self.passwords.get(key)==pw:
                self.result={"role":"Teacher","username":uname,"student_id":None}; self.destroy()
            else: messagebox.showerror("Login failed","Invalid teacher credentials.")
        else:
            sid=uname
            if sid not in self.gb.students: messagebox.showerror("Login failed","Unknown student ID."); return
            key=("student", sid)
            if self.passwords.get(key)==pw:
                self.result={"role":"Student","username":sid,"student_id":sid}; self.destroy()
            else: messagebox.showerror("Login failed","Invalid student password.")

def login_flow(root, gb, data_dir: str):
    dlg = LoginDialog(root, gb, data_dir); root.wait_window(dlg); return dlg.result

def change_password_dialog(parent, data_dir: str, role: str, username: str):
    store_path = os.path.join(data_dir, "passwords.csv")
    passwords = load_passwords_csv(store_path)
    key=("student" if role=="Student" else "teacher", username)
    if key not in passwords: messagebox.showerror("Change Password","Account not found."); return
    top=tk.Toplevel(parent); top.title("Change Password"); top.geometry("320x180"); top.resizable(False, False)
    _apply_style(top)
    frm=ttk.LabelFrame(top, text="Update Password", padding=10); frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    ttk.Label(frm, text="Current").grid(row=0, column=0, sticky="e", padx=5, pady=5); cur=tk.Entry(frm, show="•", width=22); cur.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(frm, text="New").grid(row=1, column=0, sticky="e", padx=5, pady=5); new1=tk.Entry(frm, show="•", width=22); new1.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(frm, text="Confirm").grid(row=2, column=0, sticky="e", padx=5, pady=5); new2=tk.Entry(frm, show="•", width=22); new2.grid(row=2, column=1, sticky="w", padx=5, pady=5)
    def apply():
        if cur.get()!=passwords.get(key,""): messagebox.showerror("Change Password","Current password is incorrect."); return
        if not new1.get(): messagebox.showerror("Change Password","New password cannot be empty."); return
        if new1.get()!=new2.get(): messagebox.showerror("Change Password","New passwords do not match."); return
        passwords[key]=new1.get(); save_passwords_csv(store_path, passwords); messagebox.showinfo("Change Password","Password updated."); top.destroy()
    ttk.Button(frm, text="Save", command=apply).grid(row=3, column=0, columnspan=2, pady=(10,0)); top.grab_set()
