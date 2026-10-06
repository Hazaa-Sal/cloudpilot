"""Durable local plan history with short-lived connections."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import InfrastructurePlan

@contextmanager
def connection():
    path = Path(os.environ.get("CLOUDPILOT_DB_PATH", "data/cloudpilot.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS plans (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL
        )""")
        with db:
            yield db
    finally:
        db.close()


def initialize_history() -> None:
    with connection():
        pass


def record_plan(plan: InfrastructurePlan) -> None:
    with connection() as db:
        db.execute("INSERT INTO plans (plan_id, payload) VALUES (?, ?)",
                   (plan.plan_id, plan.model_dump_json()))


def list_plans(limit: int = 25, offset: int = 0) -> list[InfrastructurePlan]:
    with connection() as db:
        rows = db.execute(
            "SELECT payload FROM plans ORDER BY sequence DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [InfrastructurePlan.model_validate_json(row[0]) for row in rows]
