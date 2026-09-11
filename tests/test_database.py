from backend.app.db.database import check_connection


def test_database_connection():
    assert check_connection() == 1