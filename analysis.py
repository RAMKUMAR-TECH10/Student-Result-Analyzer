import statistics

import database
import exam_manager
import marks_manager
import result_calculator
import student_manager
import validation


class AnalysisManager:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.students = student_manager.StudentManager(db_path)
        self.exams = exam_manager.ExamManager(db_path)
        self.marks = marks_manager.MarksManager(db_path)

    def _resolve_exam_id(self, exam_id):
        if exam_id in (None, ""):
            latest = self.exams.get_latest_exam()
            return latest["exam_id"] if latest else None
        return validation.require_exam_id(exam_id)

    def get_overview_stats(self):
        with database.get_connection(self.db_path) as connection:
            students = connection.execute(
                "SELECT COUNT(*) AS total FROM students"
            ).fetchone()["total"]
            subjects = connection.execute(
                "SELECT COUNT(*) AS total FROM subjects"
            ).fetchone()["total"]
            exams = connection.execute(
                "SELECT COUNT(*) AS total FROM examinations"
            ).fetchone()["total"]
        return {
            "total_students": students,
            "total_subjects": subjects,
            "total_exams": exams,
        }

    def get_all_results(self, exam_id=None):
        exam_id = self._resolve_exam_id(exam_id)
        if exam_id is None:
            return []
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT s.student_id, s.name, s.department, s.year "
                "FROM students s JOIN marks m ON m.student_id = s.student_id "
                "WHERE m.exam_id = ? ORDER BY s.student_id",
                (exam_id,),
            ).fetchall()

        results = []
        for student in database.rows_to_dicts(rows):
            marks = self.marks.get_student_marks(student["student_id"], exam_id)
            calculation = result_calculator.calculate_student_result(marks)
            results.append(
                {
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "department": student["department"],
                    "year": student["year"],
                    "subject_count": len(marks),
                    "total": calculation["total"],
                    "maximum_total": calculation["maximum_total"],
                    "percentage": calculation["percentage"],
                    "grade": calculation["grade"],
                    "status": calculation["status"],
                    "failed_subjects": calculation["failed_subjects"],
                }
            )
        return results

    def get_class_statistics(self, exam_id=None):
        exam_id = self._resolve_exam_id(exam_id)
        results = self.get_all_results(exam_id)
        total_students = len(results)
        passed = sum(1 for result in results if result["status"] == "Pass")
        failed = total_students - passed
        percentages = [result["percentage"] for result in results]
        average = round(statistics.mean(percentages), 2) if percentages else 0.0
        pass_percentage = (
            round((passed / total_students) * 100, 2) if total_students else 0.0
        )
        topper = max(results, key=lambda item: item["total"]) if results else None
        lowest = min(results, key=lambda item: item["total"]) if results else None

        return {
            "exam_id": exam_id,
            "total_students": total_students,
            "passed": passed,
            "failed": failed,
            "class_average": average,
            "pass_percentage": pass_percentage,
            "highest_percentage": round(max(percentages), 2) if percentages else 0.0,
            "lowest_percentage": round(min(percentages), 2) if percentages else 0.0,
            "topper": topper,
            "lowest": lowest,
        }

    def get_rankings(self, exam_id=None):
        exam_id = self._resolve_exam_id(exam_id)
        results = sorted(
            self.get_all_results(exam_id),
            key=lambda item: (-item["total"], item["student_id"]),
        )
        previous_total = None
        previous_rank = 0
        for index, result in enumerate(results, start=1):
            if result["total"] != previous_total:
                previous_rank = index
                previous_total = result["total"]
            result["rank"] = previous_rank
        return results

    def get_grade_distribution(self, exam_id=None):
        exam_id = self._resolve_exam_id(exam_id)
        distribution = {grade: 0 for grade in result_calculator.GRADE_ORDER}
        for result in self.get_all_results(exam_id):
            distribution[result["grade"]] += 1
        return distribution

    def get_subject_averages(self, exam_id=None):
        exam_id = self._resolve_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT sub.subject_id, sub.subject_name, sub.max_marks, "
                "sub.pass_marks, COUNT(m.mark_id) AS appeared, "
                "AVG(m.marks_obtained) AS average_marks, "
                "MAX(m.marks_obtained) AS highest_marks, "
                "MIN(m.marks_obtained) AS lowest_marks "
                "FROM subjects sub "
                "LEFT JOIN marks m ON m.subject_id = sub.subject_id "
                "AND m.exam_id = ? "
                "GROUP BY sub.subject_id ORDER BY sub.subject_id",
                (exam_id,),
            ).fetchall()

        averages = []
        for row in database.rows_to_dicts(rows):
            average_marks = row["average_marks"]
            averages.append(
                {
                    "subject_id": row["subject_id"],
                    "subject_name": row["subject_name"],
                    "max_marks": row["max_marks"],
                    "pass_marks": row["pass_marks"],
                    "appeared": row["appeared"],
                    "average_marks": round(average_marks, 2)
                    if average_marks is not None
                    else 0.0,
                    "highest_marks": row["highest_marks"]
                    if row["highest_marks"] is not None
                    else 0.0,
                    "lowest_marks": row["lowest_marks"]
                    if row["lowest_marks"] is not None
                    else 0.0,
                    "average_percentage": round(
                        (average_marks / row["max_marks"]) * 100, 2
                    )
                    if average_marks is not None and row["max_marks"]
                    else 0.0,
                }
            )
        return averages

    def get_student_result(self, student_id, exam_id):
        student_id = validation.require_student_id(student_id)
        exam_id = validation.require_exam_id(exam_id)
        marks = self.marks.get_student_marks(student_id, exam_id)
        if not marks:
            raise LookupError(
                "No marks found for this student in the selected examination."
            )
        student = self.students.get_student(student_id)
        calculation = result_calculator.calculate_student_result(marks)
        return {
            **student,
            **calculation,
            "exam_id": exam_id,
            "exam_name": marks[0]["exam_name"],
        }
