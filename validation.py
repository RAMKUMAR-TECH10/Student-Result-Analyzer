import re
from datetime import date, datetime

import database


class ValidationError(ValueError):
    pass


EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w.-]+\.\w+$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,19}$")


def _ensure_not_empty(value, field_name):
    if value is None or str(value).strip() == "":
        raise ValidationError(f"{field_name} is required.")
    return str(value).strip()


def require_student_id(student_id):
    student_id = _ensure_not_empty(student_id, "Student ID")
    if not ID_PATTERN.match(student_id):
        raise ValidationError("Student ID must be 2-20 chars: letters, numbers, _ or -.")
    return student_id


def require_student_name(name):
    name = _ensure_not_empty(name, "Student name")
    if name.isdigit() or not re.search(r"[A-Za-z]", name):
        raise ValidationError(
            "Student name must contain letters and cannot be only numbers."
        )
    return name


def require_email(email, optional=True):
    email = str(email or "").strip()
    if not email:
        if optional:
            return ""
        raise ValidationError("Email is required.")
    email = email.lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Enter a valid email address.")
    return email


def require_phone(phone, optional=True):
    phone = str(phone or "").strip()
    if not phone:
        if optional:
            return ""
        raise ValidationError("Phone is required.")
    if not (phone.isdigit() and len(phone) == 10):
        raise ValidationError("Phone must contain exactly 10 digits.")
    return phone


def require_department(department):
    department = _ensure_not_empty(department, "Department").upper()
    if department not in database.DEPARTMENTS:
        raise ValidationError(
            "Department must be one of: " + ", ".join(database.DEPARTMENTS) + "."
        )
    return department


def require_year(year):
    raw = _ensure_not_empty(year, "Academic year")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError("Academic year must be a whole number.")
    if not (database.YEAR_MIN <= value <= database.YEAR_MAX):
        raise ValidationError(
            f"Academic year must be between {database.YEAR_MIN} "
            f"and {database.YEAR_MAX}."
        )
    return value


def require_subject_id(subject_id):
    subject_id = _ensure_not_empty(subject_id, "Subject ID")
    if not ID_PATTERN.match(subject_id):
        raise ValidationError("Subject ID must be 2-20 chars: letters, numbers, _ or -.")
    return subject_id


def require_subject_name(subject_name):
    subject_name = _ensure_not_empty(subject_name, "Subject name")
    if subject_name.isdigit():
        raise ValidationError("Subject name cannot contain only numbers.")
    return subject_name


def require_max_marks(max_marks):
    raw = _ensure_not_empty(max_marks, "Maximum marks")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError("Maximum marks must be a positive whole number.")
    if value <= 0:
        raise ValidationError("Maximum marks must be a positive whole number.")
    return value


def require_pass_marks(pass_marks, max_marks=None):
    raw = _ensure_not_empty(pass_marks, "Passing marks")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError("Passing marks must be a whole number.")
    if value < 0:
        raise ValidationError("Passing marks cannot be negative.")
    if max_marks is not None and value > int(max_marks):
        raise ValidationError("Passing marks cannot exceed the maximum marks.")
    return value


def require_exam_id(exam_id):
    raw = _ensure_not_empty(exam_id, "Examination")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError("Examination must be a valid selection.")
    if value <= 0:
        raise ValidationError("Examination must be a valid selection.")
    return value


def require_exam_name(exam_name):
    return _ensure_not_empty(exam_name, "Examination name")


def parse_date(value, field_name):
    value = _ensure_not_empty(value, field_name)
    try:
        return datetime.strptime(value, database.DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(
            f"{field_name} must be in YYYY-MM-DD format "
            f"(e.g. {date.today().isoformat()})."
        )


def require_exam_date(exam_date):
    return parse_date(exam_date, "Examination date")


def require_marks(marks, maximum):
    raw = _ensure_not_empty(marks, "Marks")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValidationError("Marks must be numeric.")
    if value < 0:
        raise ValidationError("Marks cannot be negative.")
    if maximum is not None and value > float(maximum):
        raise ValidationError(f"Marks cannot exceed the maximum of {maximum}.")
    return round(value, 2)


def require_student_data(student_id, name, department, year, email="", phone=""):
    return {
        "student_id": require_student_id(student_id),
        "name": require_student_name(name),
        "department": require_department(department),
        "year": require_year(year),
        "email": require_email(email),
        "phone": require_phone(phone),
    }


def require_subject_data(subject_id, subject_name, max_marks, pass_marks):
    max_value = require_max_marks(max_marks)
    return {
        "subject_id": require_subject_id(subject_id),
        "subject_name": require_subject_name(subject_name),
        "max_marks": max_value,
        "pass_marks": require_pass_marks(pass_marks, max_value),
    }


def _is_valid(requirement, *args, **kwargs):
    try:
        requirement(*args, **kwargs)
        return True
    except ValidationError:
        return False


def validate_student_id(student_id):
    return _is_valid(require_student_id, student_id)


def validate_student_name(name):
    return _is_valid(require_student_name, name)


def validate_email(email):
    return _is_valid(require_email, email)


def validate_phone(phone):
    return _is_valid(require_phone, phone)


def validate_department(department):
    return _is_valid(require_department, department)


def validate_year(year):
    return _is_valid(require_year, year)


def validate_subject_id(subject_id):
    return _is_valid(require_subject_id, subject_id)


def validate_subject_name(subject_name):
    return _is_valid(require_subject_name, subject_name)


def validate_max_marks(max_marks):
    return _is_valid(require_max_marks, max_marks)


def validate_pass_marks(pass_marks, max_marks=None):
    return _is_valid(require_pass_marks, pass_marks, max_marks)


def validate_exam_name(exam_name):
    return _is_valid(require_exam_name, exam_name)


def validate_exam_date(exam_date):
    return _is_valid(require_exam_date, exam_date)


def validate_marks(marks, maximum=100):
    return _is_valid(require_marks, marks, maximum)
