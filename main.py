import argparse

import database
import gui


def main():
    parser = argparse.ArgumentParser(
        description="Student Result Analyzer Using Python"
    )
    parser.add_argument(
        "--seed", action="store_true",
        help="Add sample students, subjects, an examination and marks.",
    )
    parser.add_argument(
        "--db", default=None,
        help="Optional path to a SQLite database file.",
    )
    args = parser.parse_args()

    db_path = args.db or database.DB_PATH
    try:
        database.initialize_database(db_path)
        if args.seed:
            database.seed_sample_data(db_path)
        app = gui.StudentResultApp(db_path)
        app.mainloop()
    except Exception as error:
        database.logger.exception("Application failed to start")
        print(f"Application error: {error}")


if __name__ == "__main__":
    main()
