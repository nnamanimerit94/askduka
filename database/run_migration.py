from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in the .env file")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


with engine.begin() as connection:
    connection.execute(text(CREATE_MIGRATIONS_TABLE))

    applied_migrations = {
        row[0]
        for row in connection.execute(
            text("SELECT filename FROM schema_migrations")
        )
    }

    migration_files = sorted(
        MIGRATIONS_DIR.glob("*.sql")
    )

    for migration_file in migration_files:
        if migration_file.name in applied_migrations:
            print(f"Skipping migration: {migration_file.name}")
            continue

        print(f"Running migration: {migration_file.name}")

        sql = migration_file.read_text(encoding="utf-8")

        connection.execute(text(sql))

        connection.execute(
            text(
                """
                INSERT INTO schema_migrations (filename)
                VALUES (:filename)
                """
            ),
            {"filename": migration_file.name},
        )

        print(f"Completed: {migration_file.name}")


print("All migrations completed successfully.")
