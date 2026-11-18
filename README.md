# Student Result Analyzer Using Python

A modular desktop application that automates student academic result processing,
grade calculation, pass/fail evaluation and class performance analysis. It uses a
Tkinter graphical interface, a permanent SQLite database and Matplotlib charts.

## 1. Project description

Traditional result preparation involves manually calculating total marks,
percentages, grades and pass/fail status. This is slow and error prone. The
Student Result Analyzer stores students, subjects, examinations and marks in one
SQLite database and calculates results automatically, including the rule that a
student fails if any single subject is below its passing marks.

## 2. Objectives

- Apply modular Python programming using a separate file for each responsibility.
- Validate every important user input before saving it to the database.
- Calculate total, percentage, grade and pass/fail automatically from stored marks.
- Analyse class performance: averages, topper, pass percentage and rankings.
- Generate reports and export them to CSV and PDF.
- Handle invalid input, duplicate entries, missing records and database errors.

## 3. Features

- Student management: add, update, delete, search and list students.
- Subject management with configurable maximum and passing marks per subject.
- Examination management with dates.
- Marks entry with validation and duplicate prevention.
- Automatic result calculation (total, percentage, grade, pass/fail).
- Fail if any subject is below the passing mark, even when the percentage is high.
- Class analysis: class average, pass percentage, topper, lowest, rankings.
- Subject-wise averages, highest and lowest marks.
- Grade distribution chart (Matplotlib).
- Dashboard with summary cards and class result table.
- Individual marksheet view and PDF marksheet export.
- CSV export of class results and subject reports.
- Error logging to `student_results.log`.
- Sample data option for quick demonstrations.

### Real-time interface

- Live clock and a pulsing LIVE indicator in the header.
- Dashboard auto-refreshes every few seconds.
- Live search: tables filter as you type (no button needed).
- Live marks feedback: instant PASS/FAIL and range check while typing.
- Live class snapshot on the Marks Entry screen.
- Live validation hints on the student and subject forms.
- Marksheet and charts update automatically when a selection changes.
- Status bar shows the latest action with a timestamp.
- Clickable dashboard cards jump to the related screen.

## 4. Technologies used

| Technology | Purpose |
| --- | --- |
| Python 3.10+ | Main programming language |
| Tkinter | Graphical user interface |
| SQLite (`sqlite3`) | Data storage |
| `datetime` | Examination dates |
| `statistics` | Averages and statistical values |
| Matplotlib | Performance charts |
| ReportLab | PDF marksheet export |
| `logging` | Error log file |
| `unittest` | Unit tests |

## 5. Folder structure

```text
Student_Result_Analyzer/
├── main.py                     Application entry point
├── database.py                 SQLite connection, tables, logging and seed data
├── student_manager.py          Student operations
├── subject_manager.py          Subject operations
├── exam_manager.py             Examination operations
├── marks_manager.py            Marks entry, update and validation
├── result_calculator.py        Total, percentage, grade and pass/fail logic
├── analysis.py                 Class statistics, rankings and distributions
├── validation.py               Input validation functions
├── reports.py                  Reports, CSV export and PDF marksheets
├── gui.py                      Tkinter user interface
├── student_results.db          SQLite database (created automatically)
├── student_results.log         Error log (created automatically)
├── requirements.txt            Project dependencies
├── README.md                   This documentation
├── tests/
│   └── test_result_calculator.py   Unit tests
└── screenshots/                Application screenshots
```

## 6. Installation

```powershell
cd Student_Result_Analyzer
python --version
pip install -r requirements.txt
```

Python 3.10 or newer is required. `tkinter` and `sqlite3` are part of the
standard Python installation on Windows. Matplotlib and ReportLab are installed
from `requirements.txt`.

## 7. How to run

Start with an empty database:

```powershell
python main.py
```

Start with sample students, subjects, an examination and marks for demonstration:

```powershell
python main.py --seed
```

Use a different database file:

```powershell
python main.py --db my_results.db
```

## 8. Database information

`database.py` creates the following tables on first run.

### students

| Column | Type | Description |
| --- | --- | --- |
| student_id | TEXT | Primary key |
| name | TEXT | Student name |
| department | TEXT | Department (CSE, IT, AIDS, ...) |
| year | INTEGER | Academic year (1-5) |
| email | TEXT | Email address |
| phone | TEXT | 10-digit phone number |

### subjects

| Column | Type | Description |
| --- | --- | --- |
| subject_id | TEXT | Primary key |
| subject_name | TEXT | Subject name, unique |
| max_marks | INTEGER | Maximum marks, greater than zero |
| pass_marks | INTEGER | Minimum passing marks |

### examinations

| Column | Type | Description |
| --- | --- | --- |
| exam_id | INTEGER | Primary key (auto increment) |
| exam_name | TEXT | Examination name, unique |
| exam_date | TEXT | Examination date (YYYY-MM-DD) |

### marks

| Column | Type | Description |
| --- | --- | --- |
| mark_id | INTEGER | Primary key (auto increment) |
| student_id | TEXT | Foreign key to students |
| subject_id | TEXT | Foreign key to subjects |
| exam_id | INTEGER | Foreign key to examinations |
| marks_obtained | REAL | Marks scored, never negative |

The combination of `student_id`, `subject_id` and `exam_id` is unique, so a
student cannot have duplicate marks for the same subject and examination.
Foreign keys are enabled, and students, subjects or examinations with marks
history cannot be deleted, which protects historical records.

## 9. Grading rules

| Percentage | Grade | Result |
| --- | --- | --- |
| 90-100 | A+ | Pass |
| 80-89 | A | Pass |
| 70-79 | B | Pass |
| 60-69 | C | Pass |
| 50-59 | D | Pass |
| 40-49 | E | Pass |
| Below 40 | F | Fail |

A student also fails if any single subject mark is below that subject's passing
marks, even when the overall percentage is above 40%.

## 10. Validation and error handling

- Student, subject and examination IDs: required and unique.
- Names: required, cannot be numbers only.
- Email: standard email format (optional field).
- Phone: exactly 10 digits (optional field).
- Department: must be one of the configured departments.
- Academic year: must be within the configured range.
- Marks: numeric, not below zero and not above the subject maximum.
- Passing marks cannot exceed the maximum marks.
- Examination date: `YYYY-MM-DD`.
- Duplicate marks for the same student, subject and examination are rejected.
- Expected problems show a dialog; unexpected problems are written to
  `student_results.log`.

## 11. Testing

```powershell
python -m unittest discover -s tests -v
```

The test suite uses a temporary database and covers validation, duplicate
entries, missing records, marks ranges, result calculation, the single-subject
fail rule, class statistics, rankings, grade distribution, subject averages and
CSV/PDF export.

## 12. User interface

The application uses a light, card-based interface with a top navigation bar
(Dashboard, Students, Subjects, Examinations, Marks Entry, Results, Analysis,
Reports), an always-visible status bar and a live header clock. Charts are
embedded directly in the Analysis screen and redraw whenever data changes.

## 13. Future enhancements

- Administrator login with username and password.
- Comparison of a student's performance across multiple examinations.
- Excel export in addition to CSV.
- Email notifications of results.
- Additional charts such as subject-wise performance trends.
