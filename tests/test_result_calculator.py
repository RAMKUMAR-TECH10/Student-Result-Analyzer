import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analysis
import database
import exam_manager
import marks_manager
import reports
import result_calculator
import student_manager
import subject_manager
import validation


class TestValidation(unittest.TestCase):
    def test_valid_student_name(self):
        self.assertTrue(validation.validate_student_name("Arun"))

    def test_student_name_only_numbers(self):
        self.assertFalse(validation.validate_student_name("12345"))

    def test_valid_email(self):
        self.assertTrue(validation.validate_email("student@gmail.com"))

    def test_invalid_email(self):
        self.assertFalse(validation.validate_email("student-at-gmail.com"))

    def test_valid_phone(self):
        self.assertTrue(validation.validate_phone("9876543210"))

    def test_invalid_phone(self):
        self.assertFalse(validation.validate_phone("12345"))

    def test_valid_department(self):
        self.assertTrue(validation.validate_department("cse"))

    def test_invalid_department(self):
        self.assertFalse(validation.validate_department("Unknown"))

    def test_year_out_of_range(self):
        self.assertFalse(validation.validate_year("9"))

    def test_valid_marks(self):
        self.assertTrue(validation.validate_marks(85, 100))

    def test_marks_above_maximum(self):
        self.assertFalse(validation.validate_marks(120, 100))

    def test_negative_marks(self):
        self.assertFalse(validation.validate_marks(-5, 100))

    def test_marks_not_numeric(self):
        self.assertFalse(validation.validate_marks("abc", 100))

    def test_pass_marks_above_maximum(self):
        self.assertFalse(validation.validate_pass_marks(80, 50))


class TestResultCalculator(unittest.TestCase):
    def test_total_marks(self):
        result = result_calculator.calculate_result([80, 90, 70])
        self.assertEqual(result["total"], 240)

    def test_percentage(self):
        result = result_calculator.calculate_result([80, 90, 70])
        self.assertEqual(result["percentage"], 80.0)

    def test_grade_a_plus(self):
        result = result_calculator.calculate_result([95, 92, 90])
        self.assertEqual(result["grade"], "A+")

    def test_fail_result_when_subject_below_pass(self):
        result = result_calculator.calculate_result([80, 30, 90])
        self.assertEqual(result["status"], "Fail")
        self.assertEqual(result["grade"], "F")

    def test_grade_boundaries(self):
        self.assertEqual(result_calculator.grade_for_percentage(90), "A+")
        self.assertEqual(result_calculator.grade_for_percentage(89.9), "A")
        self.assertEqual(result_calculator.grade_for_percentage(79.9), "B")
        self.assertEqual(result_calculator.grade_for_percentage(40), "E")
        self.assertEqual(result_calculator.grade_for_percentage(39.9), "F")

    def test_empty_marks_rejected(self):
        with self.assertRaises(ValueError):
            result_calculator.calculate_result([])

    def test_student_result_uses_subject_rules(self):
        subject_marks = [
            {"subject_name": "Python", "marks_obtained": 85,
             "max_marks": 100, "pass_marks": 40},
            {"subject_name": "DBMS", "marks_obtained": 90,
             "max_marks": 100, "pass_marks": 40},
            {"subject_name": "Java", "marks_obtained": 32,
             "max_marks": 100, "pass_marks": 40},
            {"subject_name": "Mathematics", "marks_obtained": 88,
             "max_marks": 100, "pass_marks": 40},
            {"subject_name": "English", "marks_obtained": 92,
             "max_marks": 100, "pass_marks": 40},
        ]
        result = result_calculator.calculate_student_result(subject_marks)
        self.assertEqual(result["total"], 387)
        self.assertEqual(result["percentage"], 77.4)
        self.assertEqual(result["status"], "Fail")
        self.assertEqual(result["grade"], "F")
        self.assertEqual(result["failed_subjects"], ["Java"])


class TestStudentResultAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_results.db")
        database.initialize_database(self.db_path)
        self.students = student_manager.StudentManager(self.db_path)
        self.subjects = subject_manager.SubjectManager(self.db_path)
        self.exams = exam_manager.ExamManager(self.db_path)
        self.marks = marks_manager.MarksManager(self.db_path)
        self.analysis = analysis.AnalysisManager(self.db_path)
        self.reports = reports.ReportManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_sample_student(self, student_id="S101", name="Arun"):
        return self.students.add_student(student_id, name, "CSE", 2,
                                         "arun@example.com", "9876543210")

    def add_sample_subject(self, subject_id="SUB01", name="Python"):
        return self.subjects.add_subject(subject_id, name, 100, 40)

    def add_sample_exam(self):
        return self.exams.add_exam("Semester 1", "2026-04-15")

    def test_add_valid_student(self):
        student = self.add_sample_student()
        self.assertEqual(student["name"], "Arun")
        self.assertEqual(student["department"], "CSE")

    def test_add_duplicate_student_id(self):
        self.add_sample_student()
        with self.assertRaises(ValueError):
            self.add_sample_student()

    def test_generated_student_id(self):
        student = self.students.add_student("", "Kumar", "IT", 2, "", "")
        self.assertEqual(student["student_id"], "S101")

    def test_add_student_with_invalid_name(self):
        with self.assertRaises(validation.ValidationError):
            self.students.add_student("S200", "12345", "CSE", 2, "", "")

    def test_add_student_with_invalid_department(self):
        with self.assertRaises(validation.ValidationError):
            self.students.add_student("S201", "Arun", "Unknown", 2, "", "")

    def test_search_existing_student(self):
        self.add_sample_student()
        results = self.students.search_students("Arun", "name")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student_id"], "S101")

    def test_search_invalid_student(self):
        self.add_sample_student()
        with self.assertRaises(LookupError):
            self.students.get_student("S999")

    def test_add_valid_subject(self):
        subject = self.add_sample_subject()
        self.assertEqual(subject["max_marks"], 100)
        self.assertEqual(subject["pass_marks"], 40)

    def test_subject_pass_marks_above_maximum(self):
        with self.assertRaises(validation.ValidationError):
            self.subjects.add_subject("SUB09", "Physics", 50, 60)

    def test_add_exam(self):
        exam = self.add_sample_exam()
        self.assertEqual(exam["exam_name"], "Semester 1")
        self.assertEqual(exam["exam_date"], "2026-04-15")

    def test_add_exam_invalid_date(self):
        with self.assertRaises(validation.ValidationError):
            self.exams.add_exam("Semester 2", "15/04/2026")

    def test_enter_valid_marks(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        mark = self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 85)
        self.assertEqual(mark["marks_obtained"], 85)

    def test_marks_above_maximum_rejected(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        with self.assertRaises(validation.ValidationError):
            self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 120)

    def test_negative_marks_rejected(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        with self.assertRaises(validation.ValidationError):
            self.marks.enter_marks("S101", "SUB01", exam["exam_id"], -5)

    def test_duplicate_marks_rejected(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 85)
        with self.assertRaises(ValueError):
            self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 90)

    def test_marks_for_unknown_student(self):
        self.add_sample_subject()
        exam = self.add_sample_exam()
        with self.assertRaises(LookupError):
            self.marks.enter_marks("S404", "SUB01", exam["exam_id"], 50)

    def test_delete_student_with_marks_is_blocked(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 85)
        with self.assertRaises(ValueError):
            self.students.delete_student("S101")

    def test_update_marks(self):
        self.add_sample_student()
        self.add_sample_subject()
        exam = self.add_sample_exam()
        mark = self.marks.enter_marks("S101", "SUB01", exam["exam_id"], 85)
        updated = self.marks.update_marks(mark["mark_id"], 95)
        self.assertEqual(updated["marks_obtained"], 95)

    def _seed_full_exam(self):
        self.add_sample_student("S101", "Arun")
        self.add_sample_student("S102", "Kumar")
        self.add_sample_student("S103", "Priya")
        self.add_sample_student("S104", "Ravi")
        subjects = [
            ("SUB01", "Python"), ("SUB02", "DBMS"), ("SUB03", "Java"),
            ("SUB04", "Mathematics"), ("SUB05", "English"),
        ]
        for subject_id, name in subjects:
            self.subjects.add_subject(subject_id, name, 100, 40)
        exam = self.add_sample_exam()
        scores = {
            "S101": [85, 90, 78, 88, 92],
            "S102": [75, 70, 68, 72, 77],
            "S103": [96, 94, 92, 95, 94],
            "S104": [45, 38, 32, 40, 24],
        }
        for student_id, values in scores.items():
            for index, (subject_id, _) in enumerate(subjects):
                self.marks.enter_marks(
                    student_id, subject_id, exam["exam_id"], values[index]
                )
        return exam

    def test_individual_result_calculation(self):
        exam = self._seed_full_exam()
        result = self.analysis.get_student_result("S101", exam["exam_id"])
        self.assertEqual(result["total"], 433)
        self.assertEqual(result["percentage"], 86.6)
        self.assertEqual(result["grade"], "A")
        self.assertEqual(result["status"], "Pass")

    def test_fail_when_one_subject_below_pass(self):
        exam = self._seed_full_exam()
        result = self.analysis.get_student_result("S104", exam["exam_id"])
        self.assertEqual(result["status"], "Fail")
        self.assertIn("Java", result["failed_subjects"])

    def test_class_statistics(self):
        exam = self._seed_full_exam()
        stats = self.analysis.get_class_statistics(exam["exam_id"])
        self.assertEqual(stats["total_students"], 4)
        self.assertEqual(stats["passed"], 3)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["pass_percentage"], 75.0)
        self.assertEqual(stats["topper"]["student_id"], "S103")
        self.assertEqual(stats["lowest"]["student_id"], "S104")

    def test_rankings_order(self):
        exam = self._seed_full_exam()
        rankings = self.analysis.get_rankings(exam["exam_id"])
        self.assertEqual(rankings[0]["student_id"], "S103")
        self.assertEqual(rankings[0]["rank"], 1)
        self.assertEqual(rankings[-1]["student_id"], "S104")

    def test_grade_distribution(self):
        exam = self._seed_full_exam()
        distribution = self.analysis.get_grade_distribution(exam["exam_id"])
        self.assertEqual(distribution["A+"], 1)
        self.assertEqual(distribution["F"], 1)
        self.assertEqual(sum(distribution.values()), 4)

    def test_subject_averages(self):
        exam = self._seed_full_exam()
        averages = self.analysis.get_subject_averages(exam["exam_id"])
        python = next(row for row in averages if row["subject_id"] == "SUB01")
        self.assertEqual(python["appeared"], 4)
        self.assertEqual(python["average_marks"], 75.25)

    def test_export_results_csv(self):
        exam = self._seed_full_exam()
        path = os.path.join(self.temp_dir.name, "results.csv")
        saved = self.reports.export_results_csv(path, exam["exam_id"])
        self.assertTrue(os.path.exists(saved))
        with open(saved, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Student ID", content)
        self.assertIn("S103", content)

    def test_export_subject_csv(self):
        exam = self._seed_full_exam()
        path = os.path.join(self.temp_dir.name, "subjects.csv")
        saved = self.reports.export_subject_report_csv(path, exam["exam_id"])
        self.assertTrue(os.path.exists(saved))

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("reportlab"), "reportlab not installed"
    )
    def test_export_marksheet_pdf(self):
        exam = self._seed_full_exam()
        path = os.path.join(self.temp_dir.name, "marksheet.pdf")
        saved = self.reports.export_marksheet_pdf(path, "S101", exam["exam_id"])
        self.assertTrue(os.path.exists(saved))
        self.assertGreater(os.path.getsize(saved), 0)


if __name__ == "__main__":
    unittest.main()
