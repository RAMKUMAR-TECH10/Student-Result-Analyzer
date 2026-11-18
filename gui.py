from datetime import date, datetime
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import analysis
import database
import exam_manager
import marks_manager
import reports
import student_manager
import subject_manager
import validation

# ------------------------------------------------------------------ Theme
INDIGO = "#4f46e5"
INDIGO_DARK = "#4338ca"
INDIGO_SOFT = "#eef2ff"
SKY = "#0ea5e9"
TEAL = "#0d9488"
AMBER = "#f59e0b"
ROSE = "#e11d48"
GREEN = "#16a34a"
PURPLE = "#7c3aed"

BG = "#f1f5f9"
CARD = "#ffffff"
BORDER = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#64748B"
STRIPE = "#f8fafc"
FAIL_BG = "#fef2f2"
FAIL_FG = "#b91c1c"

EXPORT_DIR = os.path.join(database.BASE_DIR, "exports")

# column specs: (key, heading, width)
STUDENT_SPECS = (
    ("student_id", "Student ID", 100),
    ("name", "Name", 170),
    ("department", "Department", 110),
    ("year", "Year", 60),
    ("email", "Email", 210),
    ("phone", "Phone", 120),
)
SUBJECT_SPECS = (
    ("subject_id", "Subject ID", 110),
    ("subject_name", "Subject", 240),
    ("max_marks", "Maximum Marks", 130),
    ("pass_marks", "Passing Marks", 120),
)
EXAM_SPECS = (
    ("exam_id", "Examination ID", 140),
    ("exam_name", "Name", 320),
    ("exam_date", "Date", 150),
)
MARK_SPECS = (
    ("mark_id", "ID", 55),
    ("student_id", "Student ID", 90),
    ("name", "Name", 150),
    ("subject_id", "Subject ID", 90),
    ("subject_name", "Subject", 150),
    ("marks_obtained", "Marks", 70),
    ("max_marks", "Maximum", 80),
    ("pass_marks", "Passing", 80),
    ("status", "Status", 80),
)
RESULT_SPECS = (
    ("subject_id", "Subject ID", 110),
    ("subject_name", "Subject", 260),
    ("marks_obtained", "Marks", 100),
    ("max_marks", "Maximum", 100),
    ("pass_marks", "Passing", 100),
    ("status", "Status", 100),
)
RANK_SPECS = (
    ("rank", "Rank", 60),
    ("student_id", "Student ID", 95),
    ("name", "Name", 160),
    ("department", "Department", 110),
    ("total", "Total", 80),
    ("maximum_total", "Maximum", 85),
    ("percentage", "%", 70),
    ("grade", "Grade", 65),
    ("status", "Result", 85),
)
SUBJECT_AVG_SPECS = (
    ("subject_id", "Subject ID", 100),
    ("subject_name", "Subject", 170),
    ("appeared", "Appeared", 80),
    ("average_marks", "Average", 85),
    ("average_percentage", "Average %", 85),
    ("highest_marks", "Highest", 80),
    ("lowest_marks", "Lowest", 80),
)


def specs_columns(specs):
    return tuple(key for key, _, _ in specs)


def safe_action(action):
    def wrapped(*args, **kwargs):
        try:
            return action(*args, **kwargs)
        except (
            validation.ValidationError,
            ValueError,
            LookupError,
            RuntimeError,
        ) as error:
            messagebox.showerror("Error", str(error))
        except Exception as error:
            database.logger.exception("Unhandled error in GUI action")
            messagebox.showerror("Unexpected error", str(error))

    return wrapped


def populate_tree(tree, rows, columns, status_key=None):
    tree.delete(*tree.get_children())
    for index, row in enumerate(rows):
        tags = ("odd",) if index % 2 else ()
        if status_key and row.get(status_key) == "Fail":
            tags = ("fail",)
        tree.insert(
            "",
            "end",
            values=[
                "" if row.get(column) is None else row.get(column)
                for column in columns
            ],
            tags=tags,
        )


def selected_values(tree, columns):
    item = tree.focus()
    if not item:
        return None
    return dict(zip(columns, tree.item(item, "values")))


class StudentResultApp(tk.Tk):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        self.students = student_manager.StudentManager(db_path)
        self.subjects = subject_manager.SubjectManager(db_path)
        self.exams = exam_manager.ExamManager(db_path)
        self.marks = marks_manager.MarksManager(db_path)
        self.analysis = analysis.AnalysisManager(db_path)
        self.reports = reports.ReportManager(db_path)

        self.student_choices = {}
        self.exam_choices = {}
        self.subject_choices = {}
        self.card_labels = {}
        self.nav_buttons = {}
        self.selected_mark_id = None
        self._pending_jobs = {}
        self.current_screen = tk.StringVar(value="dashboard")

        self.title("Student Result Analyzer")
        self.geometry("1260x800")
        self.minsize(1080, 700)
        self.configure(bg=BG)

        self._configure_styles()
        self._build_header()
        self._build_statusbar()
        self._build_content()
        self.show_screen("dashboard")
        self._tick_clock()
        self._schedule_auto_refresh()

    # ------------------------------------------------------------- framework
    def _configure_styles(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure(
            "Accent.TButton", padding=6, font=("Segoe UI", 10, "bold"),
            background=INDIGO, foreground="white",
        )
        style.map("Accent.TButton", background=[("active", INDIGO_DARK)])
        style.configure("Treeview", rowheight=28, fieldbackground=CARD,
                        background=CARD, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=INDIGO_SOFT, foreground=INDIGO_DARK)
        style.configure("TCombobox", padding=4)

    def _build_header(self):
        header = tk.Frame(self, bg=CARD, height=66)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Frame(self, bg=BORDER, height=1).pack(side="top", fill="x")

        brand = tk.Frame(header, bg=CARD)
        brand.pack(side="left", padx=(20, 10))
        tk.Label(brand, text="  ", bg=INDIGO, font=("Segoe UI", 2)).pack(
            side="left", padx=(0, 8)
        )
        tk.Label(brand, text="Student Result Analyzer", bg=CARD, fg=INDIGO_DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left")

        right = tk.Frame(header, bg=CARD)
        right.pack(side="right", padx=20)
        self.live_dot = tk.Label(right, text="LIVE", bg=CARD, fg=GREEN,
                                 font=("Segoe UI", 9, "bold"))
        self.live_dot.pack(side="right", padx=(10, 0))
        self.clock_var = tk.StringVar()
        tk.Label(right, textvariable=self.clock_var, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="right")

        nav = tk.Frame(header, bg=CARD)
        nav.pack(side="left", padx=6)
        navigation = [
            ("Dashboard", "dashboard"),
            ("Students", "students"),
            ("Subjects", "subjects"),
            ("Examinations", "exams"),
            ("Marks Entry", "marks"),
            ("Results", "results"),
            ("Analysis", "analysis"),
            ("Reports", "reports"),
        ]
        for text, screen in navigation:
            button = tk.Button(
                nav, text=text, bd=0, relief="flat", padx=12, pady=7,
                bg=CARD, fg=MUTED, activebackground=INDIGO_SOFT,
                activeforeground=INDIGO_DARK, cursor="hand2",
                font=("Segoe UI", 10),
                command=lambda target=screen: self.show_screen(target),
            )
            button.pack(side="left", padx=1)
            self.nav_buttons[screen] = button

    def _build_statusbar(self):
        tk.Frame(self, bg=BORDER, height=1).pack(side="bottom", fill="x")
        bar = tk.Frame(self, bg=CARD, height=30)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=16)
        self.db_var = tk.StringVar(
            value=f"Database: {os.path.basename(self.db_path or database.DB_PATH)}"
        )
        tk.Label(bar, textvariable=self.db_var, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right", padx=16)

    def _build_content(self):
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="top", fill="both", expand=True)
        self.screens = {
            "dashboard": self._build_dashboard(),
            "students": self._build_students(),
            "subjects": self._build_subjects(),
            "exams": self._build_exams(),
            "marks": self._build_marks(),
            "results": self._build_results(),
            "analysis": self._build_analysis(),
            "reports": self._build_reports(),
        }

    def show_screen(self, name):
        self.current_screen.set(name)
        for frame in self.screens.values():
            frame.pack_forget()
        self.screens[name].pack(fill="both", expand=True)
        for screen, button in self.nav_buttons.items():
            if screen == name:
                button.configure(bg=INDIGO, fg="white",
                                 font=("Segoe UI", 10, "bold"))
            else:
                button.configure(bg=CARD, fg=MUTED, font=("Segoe UI", 10))
        refresh = getattr(self, f"refresh_{name}", None)
        if refresh:
            refresh()

    def set_status(self, message):
        self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')}  |  {message}")

    def _tick_clock(self):
        self.clock_var.set(datetime.now().strftime("%d %b %Y  %H:%M:%S"))
        self.live_dot.configure(fg=GREEN if datetime.now().second % 2 == 0 else "#86efac")
        self.after(1000, self._tick_clock)

    def _schedule_auto_refresh(self):
        if self.current_screen.get() == "dashboard":
            self.refresh_dashboard(silent=True)
        self.after(5000, self._schedule_auto_refresh)

    def _debounce(self, key, callback, delay=220):
        pending = self._pending_jobs.get(key)
        if pending is not None:
            try:
                self.after_cancel(pending)
            except Exception:
                pass
        self._pending_jobs[key] = self.after(delay, callback)

    # -------------------------------------------------------- shared widgets
    def _page_title(self, parent, title, subtitle=""):
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 6))
        tk.Label(header, text=title, bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        if subtitle:
            tk.Label(header, text=subtitle, bg=BG, fg=MUTED,
                     font=("Segoe UI", 10)).pack(side="left", padx=(12, 0), pady=(6, 0))
        return header

    def _panel(self, parent, title=None):
        panel = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                         highlightthickness=1)
        body = tk.Frame(panel, bg=CARD)
        if title:
            tk.Label(panel, text=title, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14,
                                                          pady=(10, 2))
        body.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        return panel, body

    def _field(self, parent, label, row, column, variable=None, width=24):
        variable = variable or tk.StringVar()
        tk.Label(parent, text=label, bg=CARD, fg=TEXT, font=("Segoe UI", 10)).grid(
            row=row, column=column, padx=(10, 4), pady=5, sticky="w"
        )
        ttk.Entry(parent, textvariable=variable, width=width).grid(
            row=row, column=column + 1, padx=(0, 12), pady=5, sticky="w"
        )
        return variable

    def _combo(self, parent, label, row, column, variable, values=(), width=22):
        tk.Label(parent, text=label, bg=CARD, fg=TEXT, font=("Segoe UI", 10)).grid(
            row=row, column=column, padx=(10, 4), pady=5, sticky="w"
        )
        combo = ttk.Combobox(parent, textvariable=variable, values=list(values),
                             state="readonly", width=width)
        combo.grid(row=row, column=column + 1, padx=(0, 12), pady=5, sticky="w")
        return combo

    def _make_tree(self, parent, specs, height=10):
        columns = specs_columns(specs)
        frame = ttk.Frame(parent)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        for column, heading, width in specs:
            tree.heading(column, text=heading)
            tree.column(column, width=width, anchor=tk.W)
        tree.tag_configure("odd", background=STRIPE)
        tree.tag_configure("fail", background=FAIL_BG, foreground=FAIL_FG)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return frame, tree

    @staticmethod
    def _set_choices(combo, choices, store):
        display_values = [display for display, _ in choices]
        combo.configure(values=display_values)
        store.clear()
        store.update({display: value for display, value in choices})
        if display_values:
            if combo.get() not in display_values:
                combo.set(display_values[0])
        else:
            combo.set("")

    def _bind_click(self, widget, screen):
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda event: self.show_screen(screen))
        for child in widget.winfo_children():
            self._bind_click(child, screen)

    # -------------------------------------------------------------- Dashboard
    def _build_dashboard(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Dashboard", "Live class performance overview")

        self.dashboard_exam_var = tk.StringVar()
        bar = tk.Frame(frame, bg=BG)
        bar.pack(fill="x", padx=24, pady=(0, 4))
        tk.Label(bar, text="Examination:", bg=BG, fg=TEXT).pack(side="left")
        self.dashboard_exam_combo = ttk.Combobox(
            bar, textvariable=self.dashboard_exam_var, state="readonly", width=30
        )
        self.dashboard_exam_combo.pack(side="left", padx=8)
        self.dashboard_exam_combo.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_dashboard()
        )

        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill="x", padx=18, pady=8)
        definitions = [
            ("total_students", "TOTAL STUDENTS", INDIGO, "students"),
            ("total_subjects", "TOTAL SUBJECTS", SKY, "subjects"),
            ("passed", "STUDENTS PASSED", GREEN, "analysis"),
            ("failed", "STUDENTS FAILED", ROSE, "analysis"),
            ("class_average", "CLASS AVERAGE %", AMBER, "analysis"),
            ("pass_percentage", "PASS PERCENTAGE", PURPLE, "analysis"),
        ]
        for index, (key, title, color, target) in enumerate(definitions):
            cards.columnconfigure(index, weight=1)
            card = tk.Frame(cards, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1)
            card.grid(row=0, column=index, padx=6, pady=6, sticky="nsew")
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=title, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14,
                                                        pady=(10, 0))
            value = tk.Label(card, text="0", bg=CARD, fg=color,
                             font=("Segoe UI", 26, "bold"))
            value.pack(anchor="w", padx=14, pady=(0, 8))
            self.card_labels[key] = value
            self._bind_click(card, target)

        self.dashboard_topper_var = tk.StringVar()
        tk.Label(frame, textvariable=self.dashboard_topper_var, bg=BG, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=26, pady=(2, 6))

        panel, body = self._panel(frame, "Live class results")
        panel.pack(fill="both", expand=True, padx=24, pady=(4, 18))
        tree_frame, self.dashboard_tree = self._make_tree(body, RANK_SPECS, height=11)
        tree_frame.pack(fill="both", expand=True)
        return frame

    @safe_action
    def refresh_dashboard(self, silent=False):
        self._set_choices(
            self.dashboard_exam_combo,
            [(f"{exam['exam_id']} - {exam['exam_name']}", exam["exam_id"])
             for exam in self.exams.get_all_exams()],
            self.exam_choices,
        )
        exam_id = self.exam_choices.get(self.dashboard_exam_var.get())
        stats = self.reports.get_dashboard_stats(exam_id)
        for key, value in self.card_labels.items():
            value.configure(text=str(stats.get(key, 0)))
        topper = stats.get("topper")
        if topper:
            self.dashboard_topper_var.set(
                f"Topper: {topper['name']} ({topper['student_id']})  |  "
                f"{topper['percentage']}%  |  Grade {topper['grade']}  |  "
                f"Pass percentage: {stats['pass_percentage']}%"
            )
        else:
            self.dashboard_topper_var.set(
                "No results recorded yet. Add students, subjects and marks to begin."
            )
        populate_tree(
            self.dashboard_tree,
            self.analysis.get_rankings(exam_id),
            specs_columns(RANK_SPECS),
            status_key="status",
        )
        if not silent:
            self.set_status("Dashboard refreshed.")

    # --------------------------------------------------------------- Students
    def _build_students(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Students", "Records update as you type")

        search_panel, search = self._panel(frame, "Live search")
        search_panel.pack(fill="x", padx=24, pady=(0, 6))
        tk.Label(search, text="Find:", bg=CARD, fg=TEXT).grid(row=0, column=0, padx=(2, 6))
        self.student_search_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.student_search_var, width=34).grid(
            row=0, column=1
        )
        self.student_search_field = ttk.Combobox(
            search, values=["all", "student_id", "name", "department"],
            state="readonly", width=14,
        )
        self.student_search_field.set("all")
        self.student_search_field.grid(row=0, column=2, padx=8)
        ttk.Button(search, text="Show All", command=self.refresh_students).grid(
            row=0, column=3, padx=4
        )
        self.student_search_var.trace_add(
            "write", lambda *args: self._debounce("student_search", self.search_students)
        )
        self.student_search_field.bind(
            "<<ComboboxSelected>>", lambda event: self.search_students()
        )

        form_panel, form = self._panel(frame, "Student details")
        form_panel.pack(fill="x", padx=24, pady=6)
        self.student_vars = {
            key: tk.StringVar() for key in
            ("student_id", "name", "department", "year", "email", "phone")
        }
        self._field(form, "Student ID", 0, 0, self.student_vars["student_id"])
        self._field(form, "Name", 0, 2, self.student_vars["name"], 26)
        self._combo(form, "Department", 1, 0, self.student_vars["department"],
                    database.DEPARTMENTS, width=20)
        self._combo(form, "Year", 1, 2, self.student_vars["year"],
                    [str(y) for y in range(database.YEAR_MIN, database.YEAR_MAX + 1)],
                    width=20)
        self._field(form, "Email", 2, 0, self.student_vars["email"], 28)
        self._field(form, "Phone", 2, 2, self.student_vars["phone"])

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=3, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 2))
        ttk.Button(buttons, text="Add Student", style="Accent.TButton",
                   command=self.add_student).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update", command=self.update_student).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=self.delete_student).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clear_student_form).pack(side="left", padx=3)

        self.student_hint = tk.Label(form, text="", bg=CARD, fg=MUTED,
                                     font=("Segoe UI", 9))
        self.student_hint.grid(row=4, column=0, columnspan=4, sticky="w", padx=8,
                               pady=(2, 4))
        for variable in self.student_vars.values():
            variable.trace_add("write", self.update_student_hint)

        table_panel, table = self._panel(frame, "Students")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(6, 18))
        tree_frame, self.student_tree = self._make_tree(table, STUDENT_SPECS, height=9)
        tree_frame.pack(fill="both", expand=True)
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)
        return frame

    def update_student_hint(self, *args):
        data = self.student_vars
        problems = []
        if not data["name"].get().strip():
            problems.append("Name is required")
        elif not validation.validate_student_name(data["name"].get()):
            problems.append("Name must contain letters")
        if data["department"].get() and not validation.validate_department(
            data["department"].get()
        ):
            problems.append("Choose a valid department")
        if data["year"].get() and not validation.validate_year(data["year"].get()):
            problems.append("Year must be 1-5")
        if data["email"].get() and not validation.validate_email(data["email"].get()):
            problems.append("Invalid email")
        if data["phone"].get() and not validation.validate_phone(data["phone"].get()):
            problems.append("Phone must be 10 digits")
        if problems:
            self.student_hint.configure(text="  •  ".join(problems), fg=ROSE)
        else:
            self.student_hint.configure(text="Ready to save.", fg=GREEN)

    @safe_action
    def refresh_students(self):
        populate_tree(self.student_tree, self.students.get_all_students(),
                      specs_columns(STUDENT_SPECS))
        self.set_status(f"{len(self.students.get_all_students())} student record(s).")

    @safe_action
    def search_students(self):
        query = self.student_search_var.get()
        if query.strip():
            results = self.students.search_students(query, self.student_search_field.get())
        else:
            results = self.students.get_all_students()
        populate_tree(self.student_tree, results, specs_columns(STUDENT_SPECS))
        self.set_status(f"{len(results)} match(es) for '{query}'.")

    def clear_student_form(self):
        for variable in self.student_vars.values():
            variable.set("")
        self.student_tree.selection_remove(self.student_tree.selection())
        self.update_student_hint()

    def on_student_selected(self, event=None):
        selected = selected_values(self.student_tree, specs_columns(STUDENT_SPECS))
        if selected:
            for key, variable in self.student_vars.items():
                variable.set(selected[key])

    @safe_action
    def add_student(self):
        student = self.students.add_student(
            self.student_vars["student_id"].get(),
            self.student_vars["name"].get(),
            self.student_vars["department"].get(),
            self.student_vars["year"].get(),
            self.student_vars["email"].get(),
            self.student_vars["phone"].get(),
        )
        self.set_status(f"Student '{student['name']}' added ({student['student_id']}).")
        self.clear_student_form()
        self.refresh_students()

    @safe_action
    def update_student(self):
        student = self.students.update_student(
            self.student_vars["student_id"].get(),
            self.student_vars["name"].get(),
            self.student_vars["department"].get(),
            self.student_vars["year"].get(),
            self.student_vars["email"].get(),
            self.student_vars["phone"].get(),
        )
        self.set_status(f"Student '{student['name']}' updated.")
        self.refresh_students()

    @safe_action
    def delete_student(self):
        student_id = self.student_vars["student_id"].get()
        if not messagebox.askyesno("Confirm", f"Delete student '{student_id}'?"):
            return
        self.students.delete_student(student_id)
        self.set_status(f"Student '{student_id}' deleted.")
        self.clear_student_form()
        self.refresh_students()

    # --------------------------------------------------------------- Subjects
    def _build_subjects(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Subjects", "Configure maximum and passing marks")

        form_panel, form = self._panel(frame, "Subject details")
        form_panel.pack(fill="x", padx=24, pady=(0, 6))
        self.subject_vars = {
            key: tk.StringVar() for key in
            ("subject_id", "subject_name", "max_marks", "pass_marks")
        }
        self._field(form, "Subject ID", 0, 0, self.subject_vars["subject_id"])
        self._field(form, "Subject name", 0, 2, self.subject_vars["subject_name"], 26)
        self._field(form, "Maximum marks", 1, 0, self.subject_vars["max_marks"], 12)
        self._field(form, "Passing marks", 1, 2, self.subject_vars["pass_marks"], 12)

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 2))
        ttk.Button(buttons, text="Add Subject", style="Accent.TButton",
                   command=self.add_subject).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update", command=self.update_subject).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=self.delete_subject).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clear_subject_form).pack(side="left", padx=3)

        self.subject_hint = tk.Label(form, text="", bg=CARD, fg=MUTED,
                                     font=("Segoe UI", 9))
        self.subject_hint.grid(row=3, column=0, columnspan=4, sticky="w", padx=8,
                               pady=(2, 4))
        for variable in self.subject_vars.values():
            variable.trace_add("write", self.update_subject_hint)

        table_panel, table = self._panel(frame, "Subjects")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(6, 18))
        tree_frame, self.subject_tree = self._make_tree(table, SUBJECT_SPECS, height=11)
        tree_frame.pack(fill="both", expand=True)
        self.subject_tree.bind("<<TreeviewSelect>>", self.on_subject_selected)
        return frame

    def update_subject_hint(self, *args):
        data = self.subject_vars
        problems = []
        if not data["subject_name"].get().strip():
            problems.append("Subject name is required")
        if data["max_marks"].get() and not validation.validate_max_marks(
            data["max_marks"].get()
        ):
            problems.append("Maximum marks must be a positive number")
        max_marks = data["max_marks"].get()
        if data["pass_marks"].get() and not validation.validate_pass_marks(
            data["pass_marks"].get(), max_marks if max_marks else None
        ):
            problems.append("Passing marks are invalid")
        if problems:
            self.subject_hint.configure(text="  •  ".join(problems), fg=ROSE)
        else:
            self.subject_hint.configure(text="Ready to save.", fg=GREEN)

    @safe_action
    def refresh_subjects(self):
        populate_tree(self.subject_tree, self.subjects.get_all_subjects(),
                      specs_columns(SUBJECT_SPECS))
        self.set_status(f"{len(self.subjects.get_all_subjects())} subject(s).")

    def clear_subject_form(self):
        for variable in self.subject_vars.values():
            variable.set("")
        self.subject_tree.selection_remove(self.subject_tree.selection())
        self.update_subject_hint()

    def on_subject_selected(self, event=None):
        selected = selected_values(self.subject_tree, specs_columns(SUBJECT_SPECS))
        if selected:
            for key, variable in self.subject_vars.items():
                variable.set(selected[key])

    @safe_action
    def add_subject(self):
        subject = self.subjects.add_subject(
            self.subject_vars["subject_id"].get(),
            self.subject_vars["subject_name"].get(),
            self.subject_vars["max_marks"].get(),
            self.subject_vars["pass_marks"].get(),
        )
        self.set_status(f"Subject '{subject['subject_name']}' added.")
        self.clear_subject_form()
        self.refresh_subjects()

    @safe_action
    def update_subject(self):
        subject = self.subjects.update_subject(
            self.subject_vars["subject_id"].get(),
            self.subject_vars["subject_name"].get(),
            self.subject_vars["max_marks"].get(),
            self.subject_vars["pass_marks"].get(),
        )
        self.set_status(f"Subject '{subject['subject_name']}' updated.")
        self.refresh_subjects()

    @safe_action
    def delete_subject(self):
        subject_id = self.subject_vars["subject_id"].get()
        if not messagebox.askyesno("Confirm", f"Delete subject '{subject_id}'?"):
            return
        self.subjects.delete_subject(subject_id)
        self.set_status(f"Subject '{subject_id}' deleted.")
        self.clear_subject_form()
        self.refresh_subjects()

    # ----------------------------------------------------------- Examinations
    def _build_exams(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Examinations", "Manage examination sessions")

        form_panel, form = self._panel(frame, "Examination details")
        form_panel.pack(fill="x", padx=24, pady=(0, 6))
        self.exam_vars = {
            key: tk.StringVar() for key in ("exam_id", "exam_name", "exam_date")
        }
        self._field(form, "Examination ID", 0, 0, self.exam_vars["exam_id"], 12)
        self._field(form, "Examination name", 0, 2, self.exam_vars["exam_name"], 26)
        self.exam_vars["exam_date"].set(date.today().isoformat())
        self._field(form, "Date (YYYY-MM-DD)", 1, 0, self.exam_vars["exam_date"], 20)

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 2))
        ttk.Button(buttons, text="Add Examination", style="Accent.TButton",
                   command=self.add_exam).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update", command=self.update_exam).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=self.delete_exam).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clear_exam_form).pack(side="left", padx=3)

        table_panel, table = self._panel(frame, "Examinations")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(6, 18))
        tree_frame, self.exam_tree = self._make_tree(table, EXAM_SPECS, height=11)
        tree_frame.pack(fill="both", expand=True)
        self.exam_tree.bind("<<TreeviewSelect>>", self.on_exam_selected)
        return frame

    @safe_action
    def refresh_exams(self):
        populate_tree(self.exam_tree, self.exams.get_all_exams(),
                      specs_columns(EXAM_SPECS))
        self.set_status(f"{len(self.exams.get_all_exams())} examination(s).")

    def clear_exam_form(self):
        self.exam_vars["exam_id"].set("")
        self.exam_vars["exam_name"].set("")
        self.exam_vars["exam_date"].set(date.today().isoformat())
        self.exam_tree.selection_remove(self.exam_tree.selection())

    def on_exam_selected(self, event=None):
        selected = selected_values(self.exam_tree, specs_columns(EXAM_SPECS))
        if selected:
            for key, variable in self.exam_vars.items():
                variable.set(selected[key])

    @safe_action
    def add_exam(self):
        exam = self.exams.add_exam(
            self.exam_vars["exam_name"].get(), self.exam_vars["exam_date"].get()
        )
        self.set_status(f"Examination '{exam['exam_name']}' added.")
        self.clear_exam_form()
        self.refresh_exams()

    @safe_action
    def update_exam(self):
        exam = self.exams.update_exam(
            self.exam_vars["exam_id"].get(),
            self.exam_vars["exam_name"].get(),
            self.exam_vars["exam_date"].get(),
        )
        self.set_status(f"Examination '{exam['exam_name']}' updated.")
        self.refresh_exams()

    @safe_action
    def delete_exam(self):
        exam_id = self.exam_vars["exam_id"].get()
        if not messagebox.askyesno("Confirm", f"Delete examination #{exam_id}?"):
            return
        self.exams.delete_exam(exam_id)
        self.set_status(f"Examination #{exam_id} deleted.")
        self.clear_exam_form()
        self.refresh_exams()

    # ------------------------------------------------------------ Marks entry
    def _build_marks(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Marks Entry", "Instant grading as you type")

        form_panel, form = self._panel(frame, "Enter or update marks")
        form_panel.pack(fill="x", padx=24, pady=(0, 6))
        self.mark_student_var = tk.StringVar()
        self.mark_exam_var = tk.StringVar()
        self.mark_subject_var = tk.StringVar()
        self.mark_value_var = tk.StringVar()
        self.mark_student_combo = self._combo(form, "Student", 0, 0,
                                              self.mark_student_var, width=28)
        self.mark_exam_combo = self._combo(form, "Examination", 0, 2,
                                           self.mark_exam_var, width=28)
        self.mark_subject_combo = self._combo(form, "Subject", 1, 0,
                                              self.mark_subject_var, width=28)
        self._field(form, "Marks obtained", 1, 2, self.mark_value_var, 14)

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 2))
        ttk.Button(buttons, text="Add Marks", style="Accent.TButton",
                   command=self.add_marks).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update", command=self.update_marks).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=self.delete_marks).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clear_marks_form).pack(side="left", padx=3)
        ttk.Button(buttons, text="Refresh", command=self.refresh_marks).pack(side="left", padx=3)

        self.mark_preview_var = tk.StringVar(
            value="Select a subject and type marks to see live feedback."
        )
        self.mark_preview = tk.Label(
            form, textvariable=self.mark_preview_var, bg=CARD, fg=INDIGO_DARK,
            font=("Segoe UI", 11, "bold"),
        )
        self.mark_preview.grid(row=3, column=0, columnspan=4, sticky="w", padx=8,
                               pady=(4, 2))

        self.mark_exam_var.trace_add("write", self.update_mark_preview)
        self.mark_subject_var.trace_add("write", self.update_mark_preview)
        self.mark_value_var.trace_add("write", self.update_mark_preview)
        self.mark_exam_combo.bind("<<ComboboxSelected>>", lambda event: self.load_exam_marks())

        self.mark_snapshot_var = tk.StringVar()
        tk.Label(frame, textvariable=self.mark_snapshot_var, bg=BG, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=26, pady=(2, 4))

        table_panel, table = self._panel(frame, "Marks for selected examination")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(4, 18))
        tree_frame, self.mark_tree = self._make_tree(table, MARK_SPECS, height=11)
        tree_frame.pack(fill="both", expand=True)
        self.mark_tree.bind("<<TreeviewSelect>>", self.on_mark_selected)
        return frame

    @safe_action
    def refresh_marks(self):
        self._set_choices(
            self.mark_student_combo,
            [(f"{s['student_id']} - {s['name']}", s["student_id"])
             for s in self.students.get_all_students()],
            self.student_choices,
        )
        self._set_choices(
            self.mark_exam_combo,
            [(f"{e['exam_id']} - {e['exam_name']}", e["exam_id"])
             for e in self.exams.get_all_exams()],
            self.exam_choices,
        )
        self._set_choices(
            self.mark_subject_combo,
            [(f"{s['subject_id']} - {s['subject_name']}", s["subject_id"])
             for s in self.subjects.get_all_subjects()],
            self.subject_choices,
        )
        self.load_exam_marks()

    def _selected_subject(self):
        subject_id = self.subject_choices.get(self.mark_subject_var.get())
        if not subject_id:
            return None
        return next(
            (s for s in self.subjects.get_all_subjects()
             if s["subject_id"] == subject_id),
            None,
        )

    def update_mark_preview(self, *args):
        subject = self._selected_subject()
        if subject is None:
            self.mark_preview_var.set(
                "Select a subject and type marks to see live feedback."
            )
            return
        raw = self.mark_value_var.get().strip()
        max_marks = subject["max_marks"]
        pass_marks = subject["pass_marks"]
        if raw == "":
            self.mark_preview_var.set(
                f"{subject['subject_name']}: maximum {max_marks}, passing {pass_marks}."
            )
            return
        try:
            marks = float(raw)
        except ValueError:
            self.mark_preview.configure(fg=ROSE)
            self.mark_preview_var.set("Marks must be numeric.")
            return
        if marks < 0 or marks > max_marks:
            self.mark_preview.configure(fg=ROSE)
            self.mark_preview_var.set(f"Out of range. Enter a value from 0 to {max_marks}.")
            return
        if marks >= pass_marks:
            self.mark_preview.configure(fg=GREEN)
            self.mark_preview_var.set(
                f"{subject['subject_name']}: {marks:g}/{max_marks}  ->  PASS "
                f"(passing {pass_marks})."
            )
        else:
            self.mark_preview.configure(fg=ROSE)
            self.mark_preview_var.set(
                f"{subject['subject_name']}: {marks:g}/{max_marks}  ->  FAIL "
                f"(below passing {pass_marks})."
            )

    @safe_action
    def load_exam_marks(self):
        exam_id = self.exam_choices.get(self.mark_exam_var.get())
        if not exam_id:
            populate_tree(self.mark_tree, [], specs_columns(MARK_SPECS))
            self.mark_snapshot_var.set("")
            return
        rows = self.marks.get_marks_for_exam(exam_id)
        for row in rows:
            row["status"] = "Pass" if row["marks_obtained"] >= row["pass_marks"] else "Fail"
        populate_tree(self.mark_tree, rows, specs_columns(MARK_SPECS), status_key="status")
        stats = self.analysis.get_class_statistics(exam_id)
        if stats["total_students"]:
            self.mark_snapshot_var.set(
                f"Live snapshot: {stats['total_students']} students  |  "
                f"Passed {stats['passed']}  |  Failed {stats['failed']}  |  "
                f"Class average {stats['class_average']}%"
            )
        else:
            self.mark_snapshot_var.set("No marks recorded for this examination yet.")

    def clear_marks_form(self):
        self.mark_value_var.set("")
        self.selected_mark_id = None
        self.mark_tree.selection_remove(self.mark_tree.selection())
        self.update_mark_preview()

    def on_mark_selected(self, event=None):
        selected = selected_values(self.mark_tree, specs_columns(MARK_SPECS))
        if not selected:
            return
        self.selected_mark_id = selected["mark_id"]
        student = next((d for d, v in self.student_choices.items()
                        if v == selected["student_id"]), None)
        subject = next((d for d, v in self.subject_choices.items()
                        if v == selected["subject_id"]), None)
        exam = next((d for d, v in self.exam_choices.items()
                     if str(v) == selected["exam_id"]), None)
        if student:
            self.mark_student_var.set(student)
        if subject:
            self.mark_subject_var.set(subject)
        if exam:
            self.mark_exam_var.set(exam)
        self.mark_value_var.set(selected["marks_obtained"])

    @safe_action
    def add_marks(self):
        mark = self.marks.enter_marks(
            self.student_choices.get(self.mark_student_var.get()),
            self.subject_choices.get(self.mark_subject_var.get()),
            self.exam_choices.get(self.mark_exam_var.get()),
            self.mark_value_var.get(),
        )
        self.set_status(
            f"Marks saved: {mark['name']} - {mark['subject_name']} = "
            f"{mark['marks_obtained']}/{mark['max_marks']}."
        )
        self.clear_marks_form()
        self.load_exam_marks()

    @safe_action
    def update_marks(self):
        if not self.selected_mark_id:
            raise ValueError("Select a marks row from the table to update.")
        mark = self.marks.update_marks(self.selected_mark_id, self.mark_value_var.get())
        self.set_status(
            f"Marks updated: {mark['name']} - {mark['subject_name']} = "
            f"{mark['marks_obtained']}/{mark['max_marks']}."
        )
        self.clear_marks_form()
        self.load_exam_marks()

    @safe_action
    def delete_marks(self):
        if not self.selected_mark_id:
            raise ValueError("Select a marks row from the table to delete.")
        if not messagebox.askyesno("Confirm", "Delete the selected marks entry?"):
            return
        self.marks.delete_marks(self.selected_mark_id)
        self.set_status("Marks entry deleted.")
        self.clear_marks_form()
        self.load_exam_marks()

    # ---------------------------------------------------------------- Results
    def _build_results(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Results", "Marksheet updates automatically")

        form_panel, form = self._panel(frame, "Select student and examination")
        form_panel.pack(fill="x", padx=24, pady=(0, 6))
        self.result_student_var = tk.StringVar()
        self.result_exam_var = tk.StringVar()
        self.result_student_combo = self._combo(form, "Student", 0, 0,
                                                self.result_student_var, width=30)
        self.result_exam_combo = self._combo(form, "Examination", 0, 2,
                                             self.result_exam_var, width=30)
        ttk.Button(form, text="Export Marksheet PDF", style="Accent.TButton",
                   command=self.export_marksheet_pdf).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=10, pady=6
        )
        self.result_student_var.trace_add("write", lambda *a: self.view_result())
        self.result_exam_var.trace_add("write", lambda *a: self.view_result())

        self.result_card_var = tk.StringVar(value="Select a student and examination.")
        card = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=24, pady=6)
        tk.Frame(card, bg=INDIGO, height=4).pack(fill="x")
        tk.Label(card, textvariable=self.result_card_var, bg=CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold"), justify="left").pack(
            anchor="w", padx=16, pady=12
        )

        table_panel, table = self._panel(frame, "Subject marks")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(6, 18))
        tree_frame, self.result_tree = self._make_tree(table, RESULT_SPECS, height=11)
        tree_frame.pack(fill="both", expand=True)
        return frame

    @safe_action
    def refresh_results(self):
        self._set_choices(
            self.result_student_combo,
            [(f"{s['student_id']} - {s['name']}", s["student_id"])
             for s in self.students.get_all_students()],
            self.student_choices,
        )
        self._set_choices(
            self.result_exam_combo,
            [(f"{e['exam_id']} - {e['exam_name']}", e["exam_id"])
             for e in self.exams.get_all_exams()],
            self.exam_choices,
        )
        self.view_result()

    def _current_result_selection(self):
        student_id = self.student_choices.get(self.result_student_var.get())
        exam_id = self.exam_choices.get(self.result_exam_var.get())
        if not student_id or not exam_id:
            raise ValueError("Select both a student and an examination.")
        return student_id, exam_id

    @safe_action
    def view_result(self):
        student_id = self.student_choices.get(self.result_student_var.get())
        exam_id = self.exam_choices.get(self.result_exam_var.get())
        if not student_id or not exam_id:
            self.result_card_var.set("Select a student and examination.")
            populate_tree(self.result_tree, [], specs_columns(RESULT_SPECS))
            return
        try:
            marksheet = self.reports.get_student_marksheet(student_id, exam_id)
        except LookupError as error:
            self.result_card_var.set(str(error))
            populate_tree(self.result_tree, [], specs_columns(RESULT_SPECS))
            return
        self.result_card_var.set(
            f"{marksheet['name']}  ({marksheet['student_id']})   |   "
            f"{marksheet['exam_name']}   |   {marksheet['department']} - Year {marksheet['year']}\n"
            f"Total: {marksheet['total']}/{marksheet['maximum_total']}    "
            f"Percentage: {marksheet['percentage']}%    "
            f"Grade: {marksheet['grade']}    Result: {marksheet['status']}"
            + (f"\nFailed subjects: {', '.join(marksheet['failed_subjects'])}"
               if marksheet["failed_subjects"] else "")
        )
        populate_tree(self.result_tree, marksheet["subjects"],
                      specs_columns(RESULT_SPECS), status_key="status")
        self.set_status(f"Marksheet loaded for {marksheet['name']}.")

    @safe_action
    def export_marksheet_pdf(self):
        student_id, exam_id = self._current_result_selection()
        student = self.students.get_student(student_id)
        path = filedialog.asksaveasfilename(
            title="Save marksheet as PDF",
            initialdir=EXPORT_DIR if os.path.isdir(EXPORT_DIR) else database.BASE_DIR,
            initialfile=f"marksheet_{student_id}_exam{exam_id}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return
        saved = self.reports.export_marksheet_pdf(path, student_id, exam_id)
        self.set_status(f"Marksheet for {student['name']} saved to {saved}.")

    # --------------------------------------------------------------- Analysis
    def _build_analysis(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Performance Analysis", "Statistics update live")

        bar = tk.Frame(frame, bg=BG)
        bar.pack(fill="x", padx=24, pady=(0, 4))
        tk.Label(bar, text="Examination:", bg=BG, fg=TEXT).pack(side="left")
        self.analysis_exam_var = tk.StringVar()
        self.analysis_exam_combo = ttk.Combobox(
            bar, textvariable=self.analysis_exam_var, state="readonly", width=30
        )
        self.analysis_exam_combo.pack(side="left", padx=8)
        self.analysis_exam_combo.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_analysis()
        )
        self.analysis_summary_var = tk.StringVar()
        tk.Label(frame, textvariable=self.analysis_summary_var, bg=BG, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=26, pady=(2, 6))

        body = tk.Frame(frame, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        rankings_panel, rankings = self._panel(body, "Rankings")
        rankings_panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        tree_frame, self.ranking_tree = self._make_tree(rankings, RANK_SPECS, height=8)
        tree_frame.pack(fill="both", expand=True)

        avg_panel, averages = self._panel(body, "Subject-wise average")
        avg_panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        avg_frame, self.subject_avg_tree = self._make_tree(
            averages, SUBJECT_AVG_SPECS, height=7
        )
        avg_frame.pack(fill="both", expand=True)

        chart_panel, chart = self._panel(body, "Grade distribution")
        chart_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=6, pady=6)
        self.figure = Figure(figsize=(4.6, 4.6), dpi=100, facecolor=CARD)
        self.axes = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=chart)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        return frame

    @safe_action
    def refresh_analysis(self):
        self._set_choices(
            self.analysis_exam_combo,
            [(f"{e['exam_id']} - {e['exam_name']}", e["exam_id"])
             for e in self.exams.get_all_exams()],
            self.exam_choices,
        )
        exam_id = self.exam_choices.get(self.analysis_exam_var.get())
        stats = self.analysis.get_class_statistics(exam_id)
        if stats["total_students"]:
            self.analysis_summary_var.set(
                f"Students: {stats['total_students']}   |   Passed: {stats['passed']}   |   "
                f"Failed: {stats['failed']}   |   Class average: {stats['class_average']}%   |   "
                f"Pass percentage: {stats['pass_percentage']}%   |   "
                f"Highest: {stats['highest_percentage']}%   |   Lowest: {stats['lowest_percentage']}%"
            )
        else:
            self.analysis_summary_var.set("No marks available for the selected examination.")
        populate_tree(self.ranking_tree, self.analysis.get_rankings(exam_id),
                      specs_columns(RANK_SPECS), status_key="status")
        populate_tree(self.subject_avg_tree, self.analysis.get_subject_averages(exam_id),
                      specs_columns(SUBJECT_AVG_SPECS))
        self._draw_grade_chart(self.analysis.get_grade_distribution(exam_id))
        self.set_status("Analysis updated.")

    def _draw_grade_chart(self, distribution):
        self.axes.clear()
        grades = list(distribution.keys())
        counts = list(distribution.values())
        palette = [GREEN, "#22c55e", INDIGO, SKY, AMBER, "#f59e0b", ROSE]
        bars = self.axes.bar(grades, counts, color=palette[: len(grades)], width=0.62)
        self.axes.set_title("Students per grade", color=TEXT, fontsize=11, fontweight="bold")
        self.axes.set_ylabel("Number of students", color=MUTED, fontsize=9)
        self.axes.set_xlabel("Grade", color=MUTED, fontsize=9)
        self.axes.tick_params(colors=MUTED, labelsize=9)
        for spine in ("top", "right"):
            self.axes.spines[spine].set_visible(False)
        for bar, count in zip(bars, counts):
            if count:
                self.axes.annotate(str(count), (bar.get_x() + bar.get_width() / 2, count),
                                   ha="center", va="bottom", fontsize=9, color=TEXT)
        self.figure.tight_layout()
        self.chart_canvas.draw()

    # ---------------------------------------------------------------- Reports
    def _build_reports(self):
        frame = tk.Frame(self.content, bg=BG)
        self._page_title(frame, "Reports & Export", "CSV and PDF output")

        bar = tk.Frame(frame, bg=BG)
        bar.pack(fill="x", padx=24, pady=(0, 4))
        tk.Label(bar, text="Examination:", bg=BG, fg=TEXT).pack(side="left")
        self.report_exam_var = tk.StringVar()
        self.report_exam_combo = ttk.Combobox(
            bar, textvariable=self.report_exam_var, state="readonly", width=30
        )
        self.report_exam_combo.pack(side="left", padx=8)
        self.report_exam_combo.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_reports()
        )
        self.report_summary_var = tk.StringVar()
        tk.Label(frame, textvariable=self.report_summary_var, bg=BG, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=26, pady=(2, 6))

        actions = tk.Frame(frame, bg=BG)
        actions.pack(fill="x", padx=24, pady=(0, 6))
        ttk.Button(actions, text="Export Results CSV", style="Accent.TButton",
                   command=self.export_results_csv).pack(side="left", padx=4)
        ttk.Button(actions, text="Export Subject Report CSV",
                   command=self.export_subject_csv).pack(side="left", padx=4)
        ttk.Button(actions, text="Refresh", command=self.refresh_reports).pack(
            side="left", padx=4
        )

        table_panel, table = self._panel(frame, "Class result report")
        table_panel.pack(fill="both", expand=True, padx=24, pady=(6, 18))
        tree_frame, self.report_tree = self._make_tree(table, RANK_SPECS, height=12)
        tree_frame.pack(fill="both", expand=True)
        return frame

    @safe_action
    def refresh_reports(self):
        self._set_choices(
            self.report_exam_combo,
            [(f"{e['exam_id']} - {e['exam_name']}", e["exam_id"])
             for e in self.exams.get_all_exams()],
            self.exam_choices,
        )
        exam_id = self.exam_choices.get(self.report_exam_var.get())
        stats = self.analysis.get_class_statistics(exam_id)
        if stats["total_students"]:
            self.report_summary_var.set(
                f"Students: {stats['total_students']}   |   Passed: {stats['passed']}   |   "
                f"Failed: {stats['failed']}   |   Class average: {stats['class_average']}%   |   "
                f"Pass percentage: {stats['pass_percentage']}%"
            )
        else:
            self.report_summary_var.set("No marks available for the selected examination.")
        populate_tree(self.report_tree, self.analysis.get_rankings(exam_id),
                      specs_columns(RANK_SPECS), status_key="status")
        self.set_status("Report refreshed.")

    @safe_action
    def export_results_csv(self):
        exam_id = self.exam_choices.get(self.report_exam_var.get())
        path = filedialog.asksaveasfilename(
            title="Save results as CSV",
            initialdir=EXPORT_DIR if os.path.isdir(EXPORT_DIR) else database.BASE_DIR,
            initialfile="class_results.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        saved = self.reports.export_results_csv(path, exam_id)
        self.set_status(f"Results exported to {saved}.")

    @safe_action
    def export_subject_csv(self):
        exam_id = self.exam_choices.get(self.report_exam_var.get())
        path = filedialog.asksaveasfilename(
            title="Save subject report as CSV",
            initialdir=EXPORT_DIR if os.path.isdir(EXPORT_DIR) else database.BASE_DIR,
            initialfile="subject_report.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        saved = self.reports.export_subject_report_csv(path, exam_id)
        self.set_status(f"Subject report exported to {saved}.")
