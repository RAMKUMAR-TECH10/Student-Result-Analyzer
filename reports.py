import csv
import os

import analysis
import database
import exam_manager
import marks_manager
import student_manager


class ReportManager:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.analysis = analysis.AnalysisManager(db_path)
        self.exams = exam_manager.ExamManager(db_path)
        self.marks = marks_manager.MarksManager(db_path)
        self.students = student_manager.StudentManager(db_path)

    def get_dashboard_stats(self, exam_id=None):
        stats = self.analysis.get_overview_stats()
        stats.update(self.analysis.get_class_statistics(exam_id))
        return stats

    def get_student_marksheet(self, student_id, exam_id):
        result = self.analysis.get_student_result(student_id, exam_id)
        subjects = []
        for mark in result["subjects"]:
            subjects.append(
                {
                    "subject_id": mark["subject_id"],
                    "subject_name": mark["subject_name"],
                    "marks_obtained": mark["marks_obtained"],
                    "max_marks": mark["max_marks"],
                    "pass_marks": mark["pass_marks"],
                    "status": "Pass"
                    if mark["marks_obtained"] >= mark["pass_marks"]
                    else "Fail",
                }
            )
        marksheet = dict(result)
        marksheet["subjects"] = subjects
        return marksheet

    def get_class_report(self, exam_id=None):
        return self.analysis.get_rankings(exam_id)

    def get_subject_report(self, exam_id=None):
        return self.analysis.get_subject_averages(exam_id)

    @staticmethod
    def _ensure_parent(path):
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def export_results_csv(self, path, exam_id=None):
        results = self.analysis.get_rankings(exam_id)
        if not results:
            raise ValueError("There are no results to export for this examination.")
        self._ensure_parent(path)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "Rank",
                    "Student ID",
                    "Name",
                    "Department",
                    "Year",
                    "Total",
                    "Maximum",
                    "Percentage",
                    "Grade",
                    "Result",
                    "Failed Subjects",
                ]
            )
            for result in results:
                writer.writerow(
                    [
                        result["rank"],
                        result["student_id"],
                        result["name"],
                        result["department"],
                        result["year"],
                        result["total"],
                        result["maximum_total"],
                        result["percentage"],
                        result["grade"],
                        result["status"],
                        ", ".join(result["failed_subjects"]),
                    ]
                )
        return path

    def export_subject_report_csv(self, path, exam_id=None):
        report = self.analysis.get_subject_averages(exam_id)
        if not report:
            raise ValueError("There are no subjects to export.")
        self._ensure_parent(path)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "Subject ID",
                    "Subject",
                    "Maximum Marks",
                    "Passing Marks",
                    "Appeared",
                    "Average Marks",
                    "Average %",
                    "Highest",
                    "Lowest",
                ]
            )
            for row in report:
                writer.writerow(
                    [
                        row["subject_id"],
                        row["subject_name"],
                        row["max_marks"],
                        row["pass_marks"],
                        row["appeared"],
                        row["average_marks"],
                        row["average_percentage"],
                        row["highest_marks"],
                        row["lowest_marks"],
                    ]
                )
        return path

    def export_marksheet_pdf(self, path, student_id, exam_id):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError:
            raise RuntimeError(
                "PDF export requires the 'reportlab' package. "
                "Install it with: pip install reportlab"
            )

        marksheet = self.get_student_marksheet(student_id, exam_id)
        self._ensure_parent(path)

        styles = getSampleStyleSheet()
        document = SimpleDocTemplate(path, pagesize=A4)
        elements = [
            Paragraph("Student Result Analyzer", styles["Title"]),
            Paragraph("Individual Marksheet", styles["Heading2"]),
            Spacer(1, 0.4 * cm),
        ]

        details = [
            ["Student ID", marksheet["student_id"], "Name", marksheet["name"]],
            [
                "Department",
                marksheet["department"],
                "Year",
                marksheet["year"],
            ],
            ["Examination", marksheet["exam_name"], "Result", marksheet["status"]],
        ]
        details_table = Table(details, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
        details_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(details_table)
        elements.append(Spacer(1, 0.5 * cm))

        subject_data = [
            ["Subject ID", "Subject", "Marks", "Maximum", "Passing", "Status"]
        ]
        for subject in marksheet["subjects"]:
            subject_data.append(
                [
                    subject["subject_id"],
                    subject["subject_name"],
                    subject["marks_obtained"],
                    subject["max_marks"],
                    subject["pass_marks"],
                    subject["status"],
                ]
            )
        subject_table = Table(
            subject_data,
            colWidths=[2.6 * cm, 5 * cm, 2.2 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm],
        )
        subject_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d2745")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(subject_table)
        elements.append(Spacer(1, 0.5 * cm))

        summary = [
            ["Total Marks", f"{marksheet['total']} / {marksheet['maximum_total']}"],
            ["Percentage", f"{marksheet['percentage']}%"],
            ["Grade", marksheet["grade"]],
            ["Result", marksheet["status"]],
        ]
        if marksheet["failed_subjects"]:
            summary.append(
                ["Failed Subjects", ", ".join(marksheet["failed_subjects"])]
            )
        summary_table = Table(summary, colWidths=[5 * cm, 11 * cm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(summary_table)

        document.build(elements)
        return path
