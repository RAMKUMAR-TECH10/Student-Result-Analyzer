GRADE_ORDER = ("A+", "A", "B", "C", "D", "E", "F")


def grade_for_percentage(percentage):
    if percentage >= 90:
        return "A+"
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    if percentage >= 40:
        return "E"
    return "F"


def calculate_result(marks, maximum=100, pass_mark=40):
    if not marks:
        raise ValueError("At least one subject mark is required.")

    total = sum(marks)
    maximum_total = len(marks) * maximum
    percentage = round((total / maximum_total) * 100, 2) if maximum_total else 0.0

    if any(mark < pass_mark for mark in marks):
        grade = "F"
        status = "Fail"
    else:
        grade = grade_for_percentage(percentage)
        status = "Pass"

    return {
        "total": total,
        "maximum_total": maximum_total,
        "percentage": percentage,
        "grade": grade,
        "status": status,
    }


def calculate_student_result(subject_marks):
    if not subject_marks:
        raise ValueError("No marks are available to calculate a result.")

    total = sum(record["marks_obtained"] for record in subject_marks)
    maximum_total = sum(record["max_marks"] for record in subject_marks)
    percentage = round((total / maximum_total) * 100, 2) if maximum_total else 0.0

    failed_subjects = [
        record
        for record in subject_marks
        if record["marks_obtained"] < record["pass_marks"]
    ]
    status = "Fail" if failed_subjects else "Pass"
    grade = "F" if failed_subjects else grade_for_percentage(percentage)

    return {
        "total": round(total, 2),
        "maximum_total": maximum_total,
        "percentage": percentage,
        "grade": grade,
        "status": status,
        "failed_subjects": [record["subject_name"] for record in failed_subjects],
        "subjects": subject_marks,
    }
