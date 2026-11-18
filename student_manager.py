import re

import database
import validation


class StudentManager:
    SEARCH_FIELDS = ("student_id", "name", "department")

    def __init__(self, db_path=None):
        self.db_path = db_path

    def generate_student_id(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute("SELECT student_id FROM students").fetchall()
        numbers = [
            int(match.group(1))
            for row in rows
            for match in [re.match(r"^S(\d+)$", row["student_id"])]
            if match
        ]
        return f"S{max(numbers) + 1 if numbers else 101:03d}"

    def _fetch_student(self, connection, student_id):
        row = connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"Student '{student_id}' was not found.")
        return database.row_to_dict(row)

    def add_student(self, student_id, name, department, year, email="", phone=""):
        if student_id in (None, ""):
            student_id = self.generate_student_id()
        data = validation.require_student_data(
            student_id, name, department, year, email, phone
        )
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (data["student_id"],)
            ).fetchone():
                raise ValueError(f"Student ID '{data['student_id']}' already exists.")
            connection.execute(
                "INSERT INTO students "
                "(student_id, name, department, year, email, phone) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    data["student_id"],
                    data["name"],
                    data["department"],
                    data["year"],
                    data["email"],
                    data["phone"],
                ),
            )
        return self.get_student(data["student_id"])

    def update_student(self, student_id, name, department, year, email="", phone=""):
        student_id = validation.require_student_id(student_id)
        data = validation.require_student_data(
            student_id, name, department, year, email, phone
        )
        with database.get_connection(self.db_path) as connection:
            self._fetch_student(connection, student_id)
            connection.execute(
                "UPDATE students SET name = ?, department = ?, year = ?, "
                "email = ?, phone = ? WHERE student_id = ?",
                (
                    data["name"],
                    data["department"],
                    data["year"],
                    data["email"],
                    data["phone"],
                    student_id,
                ),
            )
        return self.get_student(student_id)

    def delete_student(self, student_id):
        student_id = validation.require_student_id(student_id)
        with database.get_connection(self.db_path) as connection:
            self._fetch_student(connection, student_id)
            history = connection.execute(
                "SELECT COUNT(*) AS count FROM marks WHERE student_id = ?",
                (student_id,),
            ).fetchone()["count"]
            if history:
                raise ValueError(
                    "Cannot delete a student with marks history. "
                    "Keeping history is required for reports."
                )
            connection.execute(
                "DELETE FROM students WHERE student_id = ?", (student_id,)
            )

    def get_student(self, student_id):
        student_id = validation.require_student_id(student_id)
        with database.get_connection(self.db_path) as connection:
            return self._fetch_student(connection, student_id)

    def get_all_students(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM students ORDER BY student_id"
            ).fetchall()
        return database.rows_to_dicts(rows)

    def search_students(self, query, field="all"):
        if field != "all" and field not in self.SEARCH_FIELDS:
            raise ValueError("Invalid search field for students.")
        query = str(query or "").strip()
        with database.get_connection(self.db_path) as connection:
            if field == "all":
                sql = (
                    "SELECT * FROM students WHERE student_id LIKE ? OR name LIKE ? "
                    "OR department LIKE ? ORDER BY student_id"
                )
                params = [f"%{query}%"] * 3
            else:
                sql = f"SELECT * FROM students WHERE {field} LIKE ? ORDER BY student_id"
                params = [f"%{query}%"]
            rows = connection.execute(sql, params).fetchall()
        return database.rows_to_dicts(rows)
