import database
import validation


class ExamManager:
    SEARCH_FIELDS = ("exam_name", "exam_date")

    def __init__(self, db_path=None):
        self.db_path = db_path

    def _fetch_exam(self, connection, exam_id):
        row = connection.execute(
            "SELECT * FROM examinations WHERE exam_id = ?", (exam_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"Examination #{exam_id} was not found.")
        return database.row_to_dict(row)

    def add_exam(self, exam_name, exam_date):
        name = validation.require_exam_name(exam_name)
        date_value = validation.require_exam_date(exam_date)
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM examinations WHERE exam_name = ?", (name,)
            ).fetchone():
                raise ValueError(f"Examination '{name}' already exists.")
            exam_id = connection.execute(
                "INSERT INTO examinations (exam_name, exam_date) VALUES (?, ?)",
                (name, date_value.isoformat()),
            ).lastrowid
        return self.get_exam(exam_id)

    def update_exam(self, exam_id, exam_name, exam_date):
        exam_id = validation.require_exam_id(exam_id)
        name = validation.require_exam_name(exam_name)
        date_value = validation.require_exam_date(exam_date)
        with database.get_connection(self.db_path) as connection:
            self._fetch_exam(connection, exam_id)
            if connection.execute(
                "SELECT 1 FROM examinations WHERE exam_name = ? AND exam_id <> ?",
                (name, exam_id),
            ).fetchone():
                raise ValueError(f"Examination '{name}' already exists.")
            connection.execute(
                "UPDATE examinations SET exam_name = ?, exam_date = ? "
                "WHERE exam_id = ?",
                (name, date_value.isoformat(), exam_id),
            )
        return self.get_exam(exam_id)

    def delete_exam(self, exam_id):
        exam_id = validation.require_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            self._fetch_exam(connection, exam_id)
            history = connection.execute(
                "SELECT COUNT(*) AS count FROM marks WHERE exam_id = ?", (exam_id,)
            ).fetchone()["count"]
            if history:
                raise ValueError(
                    "Cannot delete an examination with marks history. "
                    "Keeping history is required for reports."
                )
            connection.execute(
                "DELETE FROM examinations WHERE exam_id = ?", (exam_id,)
            )

    def get_exam(self, exam_id):
        exam_id = validation.require_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            return self._fetch_exam(connection, exam_id)

    def get_all_exams(self):
        with database.get_connection(self.db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM examinations ORDER BY exam_date DESC, exam_id DESC"
            ).fetchall()
        return database.rows_to_dicts(rows)

    def get_latest_exam(self):
        with database.get_connection(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM examinations ORDER BY exam_date DESC, exam_id DESC "
                "LIMIT 1"
            ).fetchone()
        return database.row_to_dict(row)

    def search_exams(self, query, field="all"):
        if field != "all" and field not in self.SEARCH_FIELDS:
            raise ValueError("Invalid search field for examinations.")
        query = str(query or "").strip()
        with database.get_connection(self.db_path) as connection:
            if field == "all":
                sql = (
                    "SELECT * FROM examinations WHERE exam_name LIKE ? "
                    "OR exam_date LIKE ? ORDER BY exam_date DESC"
                )
                params = [f"%{query}%"] * 2
            else:
                sql = (
                    f"SELECT * FROM examinations WHERE {field} LIKE ? "
                    "ORDER BY exam_date DESC"
                )
                params = [f"%{query}%"]
            rows = connection.execute(sql, params).fetchall()
        return database.rows_to_dicts(rows)
