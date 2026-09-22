"""Local, append-only execution storage. Database paths are application configuration."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from aerotest.runner import SimulationResult, _decode


class StoredExecution(BaseModel):
    execution_id: str
    created_at: datetime
    result: SimulationResult


class RunStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("unsupported run database version")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )
            """)
            connection.execute("PRAGMA user_version = 1")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def save(self, result: SimulationResult) -> StoredExecution:
        # Snapshot and revalidate before opening a write transaction.
        raw = result.model_dump_json()
        validated = _decode(raw.encode(), result.config)
        execution = StoredExecution(execution_id=str(uuid4()), created_at=datetime.now(UTC),
                                    result=validated)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO executions (execution_id, created_at, result_json) VALUES (?, ?, ?)",
                (execution.execution_id, execution.created_at.isoformat(), raw),
            )
        return execution

    def get(self, execution_id: str) -> StoredExecution | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT created_at, result_json FROM executions WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
        if row is None:
            return None
        result = SimulationResult.model_validate_json(row[1])
        result = _decode(row[1].encode(), result.config)
        return StoredExecution(execution_id=execution_id, created_at=row[0], result=result)
