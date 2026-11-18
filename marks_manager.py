import database
import validation


class MarksManager:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def _fetch_mark(self, connection, mark_id):
        row = connection.execute(
            "SELECT m.mark_id, m.student_id, s.name, m.subject_id, sub.subject_name, "
            "m.exam_id, e.exam_name, m.marks_obtained, sub.max_marks, sub.pass_marks "
            "FROM marks m "
            "JOIN students s ON s.student_id = m.student_id "
            "JOIN subjects sub ON sub.subject_id = m.subject_id "
            "JOIN examinations e ON e.exam_id = m.exam_id "
            "WHERE m.mark_id = ?",
            (mark_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"Marks entry #{mark_id} was not found.")
        return database.row_to_dict(row)

    def enter_marks(self, student_id, subject_id, exam_id, marks_obtained):
        student_id = validation.require_student_id(student_id)
        subject_id = validation.require_subject_id(subject_id)
        exam_id = validation.require_exam_id(exam_id)

        with database.get_connection(self.db_path) as connection:
            student = connection.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if student is None:
                raise LookupError(f"Student '{student_id}' was not found.")
            subject = connection.execute(
                "SELECT max_marks FROM subjects WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            if subject is None:
                raise LookupError(f"Subject '{subject_id}' was not found.")
            exam = connection.execute(
                "SELECT 1 FROM examinations WHERE exam_id = ?", (exam_id,)
            ).fetchone()
            if exam is None:
                raise LookupError(f"Examination #{exam_id} was not found.")

            value = validation.require_marks(marks_obtained, subject["max_marks"])

            if connection.execute(
                "SELECT 1 FROM marks WHERE student_id = ? AND subject_id = ? "
                "AND exam_id = ?",
                (student_id, subject_id, exam_id),
            ).fetchone():
                raise ValueError(
                    "Marks already exist for this student, subject and examination. "
                    "Update the existing entry instead."
                )

            mark_id = connection.execute(
                "INSERT INTO marks "
                "(student_id, subject_id, exam_id, marks_obtained) "
                "VALUES (?, ?, ?, ?)",
                (student_id, subject_id, exam_id, value),
            ).lastrowid
            result = self._fetch_mark(connection, mark_id)
        return result

    def update_marks(self, mark_id, marks_obtained):
        mark_id = self._require_mark_id(mark_id)
        with database.get_connection(self.db_path) as connection:
            mark = self._fetch_mark(connection, mark_id)
            value = validation.require_marks(marks_obtained, mark["max_marks"])
            connection.execute(
                "UPDATE marks SET marks_obtained = ? WHERE mark_id = ?",
                (value, mark_id),
            )
            result = self._fetch_mark(connection, mark_id)
        return result

    def delete_marks(self, mark_id):
        mark_id = self._require_mark_id(mark_id)
        with database.get_connection(self.db_path) as connection:
            self._fetch_mark(connection, mark_id)
            connection.execute("DELETE FROM marks WHERE mark_id = ?", (mark_id,))

    def get_mark(self, mark_id):
        mark_id = self._require_mark_id(mark_id)
        with database.get_connection(self.db_path) as connection:
            return self._fetch_mark(connection, mark_id)

    def get_student_marks(self, student_id, exam_id=None):
        student_id = validation.require_student_id(student_id)
        if exam_id not in (None, ""):
            exam_id = validation.require_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone() is None:
                raise LookupError(f"Student '{student_id}' was not found.")
            sql = (
                "SELECT m.mark_id, m.student_id, sub.subject_id, sub.subject_name, "
                "m.exam_id, e.exam_name, m.marks_obtained, sub.max_marks, "
                "sub.pass_marks "
                "FROM marks m "
                "JOIN subjects sub ON sub.subject_id = m.subject_id "
                "JOIN examinations e ON e.exam_id = m.exam_id "
                "WHERE m.student_id = ? "
            )
            params = [student_id]
            if exam_id not in (None, ""):
                sql += "AND m.exam_id = ? "
                params.append(exam_id)
            sql += "ORDER BY sub.subject_id"
            rows = connection.execute(sql, params).fetchall()
        return database.rows_to_dicts(rows)

    def get_marks_for_exam(self, exam_id):
        exam_id = validation.require_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM examinations WHERE exam_id = ?", (exam_id,)
            ).fetchone() is None:
                raise LookupError(f"Examination #{exam_id} was not found.")
            rows = connection.execute(
                "SELECT m.mark_id, m.student_id, s.name, m.subject_id, "
                "sub.subject_name, m.exam_id, e.exam_name, m.marks_obtained, "
                "sub.max_marks, sub.pass_marks "
                "FROM marks m "
                "JOIN students s ON s.student_id = m.student_id "
                "JOIN subjects sub ON sub.subject_id = m.subject_id "
                "JOIN examinations e ON e.exam_id = m.exam_id "
                "WHERE m.exam_id = ? "
                "ORDER BY m.student_id, sub.subject_id",
                (exam_id,),
            ).fetchall()
        return database.rows_to_dicts(rows)

    def get_subject_marks(self, subject_id, exam_id=None):
        subject_id = validation.require_subject_id(subject_id)
        if exam_id not in (None, ""):
            exam_id = validation.require_exam_id(exam_id)
        with database.get_connection(self.db_path) as connection:
            if connection.execute(
                "SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)
            ).fetchone() is None:
                raise LookupError(f"Subject '{subject_id}' was not found.")
            sql = (
                "SELECT m.mark_id, m.student_id, s.name, m.subject_id, "
                "sub.subject_name, m.exam_id, e.exam_name, m.marks_obtained, "
                "sub.max_marks, sub.pass_marks "
                "FROM marks m "
                "JOIN students s ON s.student_id = m.student_id "
                "JOIN subjects sub ON sub.subject_id = m.subject_id "
                "JOIN examinations e ON e.exam_id = m.exam_id "
                "WHERE m.subject_id = ? "
            )
            params = [subject_id]
            if exam_id not in (None, ""):
                sql += "AND m.exam_id = ? "
                params.append(exam_id)
            sql += "ORDER BY m.student_id"
            rows = connection.execute(sql, params).fetchall()
        return database.rows_to_dicts(rows)

    @staticmethod
    def _require_mark_id(mark_id):
        raw = str(mark_id or "").strip()
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise validation.ValidationError("Marks entry must be a valid selection.")
        if value <= 0:
            raise validation.ValidationError("Marks entry must be a valid selection.")
        return value
