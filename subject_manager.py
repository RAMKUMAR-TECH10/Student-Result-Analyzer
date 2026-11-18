import re

import database
import validation


class SubjectManager:
    SEARCH_FIELDS = ("subject_id", "subject_name")

    def __init__(self, db_path=None):
        self.db_path = db_path

    def generate_subject_id(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute("SELECT subject_id FROM subjects").fetchall()
        numbers = [
            int(match.group(1))
            for row in rows
            for match in [re.match(r"^SUB(\d+)$", row["subject_id"])]
            if match
        ]
        return f"SUB{max(numbers) + 1 if numbers else 1:02d}"

    def _fetch_subject(self, connection, subject_id):
        row = connection.execute(
            "SELECT * FROM subjects WHERE subject_id = ?", (subject_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"Subject '{subject_id}' was not found.")
        return database.row_to_dict(row)

    def add_subject(self, subject_id, subject_name, max_marks, pass_marks):
        if subject_id in (None, ""):
            subject_id = self.generate_subject_id()
        data = validation.require_subject_data(
            subject_id, subject_name, max_marks, pass_marks
        )
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM subjects WHERE subject_id = ?", (data["subject_id"],)
            ).fetchone():
                raise ValueError(f"Subject ID '{data['subject_id']}' already exists.")
            if connection.execute(
                "SELECT 1 FROM subjects WHERE subject_name = ?",
                (data["subject_name"],),
            ).fetchone():
                raise ValueError(
                    f"Subject '{data['subject_name']}' already exists."
                )
            connection.execute(
                "INSERT INTO subjects "
                "(subject_id, subject_name, max_marks, pass_marks) "
                "VALUES (?, ?, ?, ?)",
                (
                    data["subject_id"],
                    data["subject_name"],
                    data["max_marks"],
                    data["pass_marks"],
                ),
            )
        return self.get_subject(data["subject_id"])

    def update_subject(self, subject_id, subject_name, max_marks, pass_marks):
        subject_id = validation.require_subject_id(subject_id)
        data = validation.require_subject_data(
            subject_id, subject_name, max_marks, pass_marks
        )
        with database.get_connection(self.db_path) as connection:
            self._fetch_subject(connection, subject_id)
            if connection.execute(
                "SELECT 1 FROM subjects WHERE subject_name = ? AND subject_id <> ?",
                (data["subject_name"], subject_id),
            ).fetchone():
                raise ValueError(
                    f"Subject '{data['subject_name']}' already exists."
                )
            connection.execute(
                "UPDATE subjects SET subject_name = ?, max_marks = ?, "
                "pass_marks = ? WHERE subject_id = ?",
                (
                    data["subject_name"],
                    data["max_marks"],
                    data["pass_marks"],
                    subject_id,
                ),
            )
        return self.get_subject(subject_id)

    def delete_subject(self, subject_id):
        subject_id = validation.require_subject_id(subject_id)
        with database.get_connection(self.db_path) as connection:
            self._fetch_subject(connection, subject_id)
            history = connection.execute(
                "SELECT COUNT(*) AS count FROM marks WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()["count"]
            if history:
                raise ValueError(
                    "Cannot delete a subject with marks history. "
                    "Keeping history is required for reports."
                )
            connection.execute(
                "DELETE FROM subjects WHERE subject_id = ?", (subject_id,)
            )

    def get_subject(self, subject_id):
        subject_id = validation.require_subject_id(subject_id)
        with database.get_connection(self.db_path) as connection:
            return self._fetch_subject(connection, subject_id)

    def get_all_subjects(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM subjects ORDER BY subject_id"
            ).fetchall()
        return database.rows_to_dicts(rows)

    def search_subjects(self, query, field="all"):
        if field != "all" and field not in self.SEARCH_FIELDS:
            raise ValueError("Invalid search field for subjects.")
        query = str(query or "").strip()
        with database.get_connection(self.db_path) as connection:
            if field == "all":
                sql = (
                    "SELECT * FROM subjects WHERE subject_id LIKE ? "
                    "OR subject_name LIKE ? ORDER BY subject_id"
                )
                params = [f"%{query}%"] * 2
            else:
                sql = (
                    f"SELECT * FROM subjects WHERE {field} LIKE ? ORDER BY subject_id"
                )
                params = [f"%{query}%"]
            rows = connection.execute(sql, params).fetchall()
        return database.rows_to_dicts(rows)
