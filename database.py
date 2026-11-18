import logging
import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "student_results.db")
LOG_PATH = os.path.join(BASE_DIR, "student_results.log")

DATE_FORMAT = "%Y-%m-%d"
DEFAULT_MAX_MARKS = 100
DEFAULT_PASS_MARKS = 40
DEPARTMENTS = ("CSE", "IT", "AIDS", "ECE", "EEE", "MECH", "CIVIL", "MBA")
YEAR_MIN = 1
YEAR_MAX = 5

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("student_results")


def connect(db_path=None):
    path = db_path or DB_PATH
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def get_connection(db_path=None):
    connection = None
    try:
        connection = connect(db_path)
        yield connection
        connection.commit()
    except Exception as error:
        if connection is not None:
            connection.rollback()
        if isinstance(error, sqlite3.Error):
            logger.exception("Database transaction failed")
        raise
    finally:
        if connection is not None:
            connection.close()


def initialize_database(db_path=None):
    try:
        with get_connection(db_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    year INTEGER NOT NULL CHECK (year >= 1),
                    email TEXT,
                    phone TEXT
                );

                CREATE TABLE IF NOT EXISTS subjects (
                    subject_id TEXT PRIMARY KEY,
                    subject_name TEXT NOT NULL UNIQUE,
                    max_marks INTEGER NOT NULL CHECK (max_marks > 0),
                    pass_marks INTEGER NOT NULL CHECK (pass_marks >= 0)
                );

                CREATE TABLE IF NOT EXISTS examinations (
                    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_name TEXT NOT NULL UNIQUE,
                    exam_date TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS marks (
                    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    exam_id INTEGER NOT NULL,
                    marks_obtained REAL NOT NULL CHECK (marks_obtained >= 0),
                    UNIQUE (student_id, subject_id, exam_id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id)
                        ON DELETE RESTRICT,
                    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
                        ON DELETE RESTRICT,
                    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
                        ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
                CREATE INDEX IF NOT EXISTS idx_students_department ON students(department);
                CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
                CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject_id);
                CREATE INDEX IF NOT EXISTS idx_marks_exam ON marks(exam_id);
                """
            )
    except sqlite3.Error:
        logger.exception("Could not initialize the database")
        raise


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def seed_sample_data(db_path=None):
    students = [
        ("S101", "Arun", "CSE", 2, "arun@example.com", "9876543210"),
        ("S102", "Kumar", "IT", 2, "kumar@example.com", "9876543211"),
        ("S103", "Priya", "AIDS", 2, "priya@example.com", "9876543212"),
        ("S104", "Ravi", "CSE", 2, "ravi@example.com", "9876543213"),
    ]
    subjects = [
        ("SUB01", "Python", 100, 40),
        ("SUB02", "DBMS", 100, 40),
        ("SUB03", "Java", 100, 40),
        ("SUB04", "Mathematics", 100, 40),
        ("SUB05", "English", 100, 40),
    ]
    sample_marks = {
        "S101": [85, 90, 78, 88, 92],
        "S102": [75, 70, 68, 72, 77],
        "S103": [96, 94, 92, 95, 94],
        "S104": [45, 38, 32, 40, 24],
    }
    with get_connection(db_path) as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO students "
            "(student_id, name, department, year, email, phone) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            students,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO subjects "
            "(subject_id, subject_name, max_marks, pass_marks) VALUES (?, ?, ?, ?)",
            subjects,
        )
        connection.execute(
            "INSERT OR IGNORE INTO examinations (exam_name, exam_date) "
            "VALUES (?, ?)",
            ("Semester 1", "2026-04-15"),
        )
        exam_row = connection.execute(
            "SELECT exam_id FROM examinations WHERE exam_name = ?", ("Semester 1",)
        ).fetchone()
        exam_id = exam_row["exam_id"]
        for student_id, scores in sample_marks.items():
            for index, subject in enumerate(subjects):
                connection.execute(
                    "INSERT OR IGNORE INTO marks "
                    "(student_id, subject_id, exam_id, marks_obtained) "
                    "VALUES (?, ?, ?, ?)",
                    (student_id, subject[0], exam_id, scores[index]),
                )
