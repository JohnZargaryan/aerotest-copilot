import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest

from aerotest.contracts import SimulationConfig
from aerotest.runner import RunnerError, run_simulation
from aerotest.storage import RunStore


@pytest.fixture
def result():
    return asyncio.run(run_simulation(
        SimulationConfig(scenario_id="healthy-baseline", duration_ms=1000)))


def test_round_trip_survives_reopening(tmp_path, result):
    path = tmp_path / "nested" / "runs.sqlite"
    before = datetime.now(UTC)
    saved = RunStore(path).save(result)
    loaded = RunStore(path).get(saved.execution_id)
    assert loaded == saved
    assert before <= loaded.created_at <= datetime.now(UTC)
    assert loaded.result.model_dump() == result.model_dump()


def test_replays_have_distinct_execution_ids(tmp_path, result):
    store = RunStore(tmp_path / "runs.sqlite")
    first, second = store.save(result), store.save(result)
    assert first.execution_id != second.execution_id
    assert first.result == second.result
    assert store.get(first.execution_id) == first
    assert store.get(second.execution_id) == second


def test_missing_and_sql_input_are_not_queries(tmp_path, result):
    store = RunStore(tmp_path / "runs.sqlite")
    saved = store.save(result)
    assert store.get("absent") is None
    assert store.get("' OR 1=1 --") is None
    assert store.get(saved.execution_id) == saved


def test_invalid_result_is_not_saved(tmp_path, result):
    path = tmp_path / "runs.sqlite"
    store = RunStore(path)
    result.records[0].event_id = "corrupted"
    with pytest.raises(RunnerError, match="INVALID_RESULT"):
        store.save(result)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM executions").fetchone()[0] == 0


def test_save_is_a_snapshot(tmp_path, result):
    store = RunStore(tmp_path / "runs.sqlite")
    saved = store.save(result)
    result.records[0].event_id = "changed later"
    assert store.get(saved.execution_id) == saved


def test_concurrent_saves_do_not_overwrite(tmp_path, result):
    store = RunStore(tmp_path / "runs.sqlite")
    with ThreadPoolExecutor(max_workers=4) as pool:
        saved = list(pool.map(lambda _: store.save(result), range(8)))
    assert len({item.execution_id for item in saved}) == 8
    assert all(store.get(item.execution_id) == item for item in saved)


def test_future_database_version_is_preserved(tmp_path):
    path = tmp_path / "runs.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version = 2")
    with pytest.raises(ValueError, match="unsupported"):
        RunStore(path)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
