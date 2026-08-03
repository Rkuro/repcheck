"""Shared test fixtures.

There is no Postgres in the test environment, and `app.database.database` builds a
real engine and calls `SQLModel.metadata.create_all()` at *import* time, so the
engine, the dotenv read, and the rotating logfile all have to be stubbed out before
the app package is imported. Everything below that point runs against a fake session
injected through FastAPI's `dependency_overrides`.
"""

import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import NoResultFound

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Must be set before app.database.database is imported: it calls quote() on this and
# would raise on None. The value is never used because create_engine is mocked out.
os.environ.setdefault("POSTGRES_DB_PASSWORD", "unused-in-tests")

with mock.patch("dotenv.load_dotenv"), \
        mock.patch("sqlmodel.create_engine", return_value=mock.MagicMock()), \
        mock.patch("sqlalchemy.MetaData.create_all"), \
        mock.patch(
            "logging.handlers.TimedRotatingFileHandler",
            return_value=logging.NullHandler(),
        ):
    from app.database.database import get_session
    from app.main import app


class FakeResult:
    """Stands in for a SQLAlchemy/SQLModel Result over a fixed list of rows."""

    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)

    def fetchall(self):
        return list(self._rows)

    def one(self):
        if not self._rows:
            raise NoResultFound("No row was found when one was required")
        return self._rows[0]

    def one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeQuery:
    """Stands in for the legacy `session.query(...)` chain used by areas.py."""

    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self._rows)


class FakeSession:
    """Records every statement it is handed and replays canned result rows in order.

    `results` is a list of row-lists, one per exec()/execute() call the handler makes.
    Calls past the end of the list yield no rows.
    """

    def __init__(self, results=None, query_rows=()):
        self._results = list(results or [])
        self._query_rows = list(query_rows)
        self.statements = []

    def _next(self, statement):
        self.statements.append(statement)
        rows = self._results.pop(0) if self._results else []
        return FakeResult(rows)

    def exec(self, statement, *_args, **_kwargs):
        return self._next(statement)

    def execute(self, statement, *_args, **_kwargs):
        return self._next(statement)

    def query(self, *_args, **_kwargs):
        return FakeQuery(self._query_rows)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def client():
    """TestClient whose session dependency is overridden per-test via `use_session`."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def use_session():
    """Install a FakeSession as the app's session dependency; returns the session."""

    def _install(results=None, query_rows=()):
        session = FakeSession(results=results, query_rows=query_rows)
        app.dependency_overrides[get_session] = lambda: session
        return session

    yield _install
    app.dependency_overrides.clear()


def compile_statement(statement):
    """Compile a recorded statement against the Postgres dialect."""
    return statement.compile(dialect=postgresql.dialect())


def find_statement(session, needle):
    """Return the (sql_text, params) of the first recorded statement containing `needle`."""
    for statement in session.statements:
        if not hasattr(statement, "compile"):
            continue
        compiled = compile_statement(statement)
        sql = str(compiled)
        if needle in sql:
            return sql, compiled.params
    raise AssertionError(
        f"No recorded statement contained {needle!r}. "
        f"Recorded {len(session.statements)} statement(s)."
    )


def fake_area(centroid_lat=40.0, centroid_lon=-74.0):
    """Minimal duck-typed stand-in for an Area row (handlers only read the centroid)."""
    return SimpleNamespace(
        id="ocd-division/country:us/zipcode:12345",
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
    )
