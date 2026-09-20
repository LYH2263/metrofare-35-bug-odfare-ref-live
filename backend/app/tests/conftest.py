import pytest

from app import db, seed
from app.services.metro_service import MetroService


@pytest.fixture
def service(tmp_path, monkeypatch):
    # Point the engine at an isolated, freshly seeded SQLite file per test.
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


@pytest.fixture
def count_runs(service):
    def _count() -> int:
        return service._conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]

    return _count
