import importlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aerotest.app import create_app
from aerotest.runner import RunnerError

api_module = importlib.import_module("aerotest.app")


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                      "missing-messages", "battery-degradation"])
def test_create_and_retrieve_after_restart(tmp_path, scenario):
    path = tmp_path / "runs.sqlite"
    with TestClient(create_app(path)) as client:
        response = client.post("/api/v1/runs", json={"scenario_id": scenario})
    assert response.status_code == 201
    body = response.json()
    assert body["result"]["config"]["scenario_id"] == scenario
    with TestClient(create_app(path)) as restarted:
        loaded = restarted.get(response.headers["Location"])
    assert loaded.status_code == 200
    assert loaded.json() == body


def test_invalid_and_missing_ids(tmp_path):
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    assert client.get("/api/v1/runs/not-a-uuid").status_code == 422
    assert client.get(f"/api/v1/runs/{uuid4()}").status_code == 404
    assert client.post("/api/v1/runs", json={"scenario_id": "bad"}).status_code == 422


@pytest.mark.parametrize("code,status", [("TIMEOUT", 504), ("START_FAILED", 503),
                                         ("PROCESS_FAILED", 502), ("OUTPUT_LIMIT", 502)])
def test_runner_failure_does_not_persist(tmp_path, monkeypatch, code, status):
    async def fail(config):
        raise RunnerError(code)
    monkeypatch.setattr(api_module, "run_simulation", fail)
    path = tmp_path / "runs.sqlite"
    client = TestClient(create_app(path))
    for _ in range(3):  # Failure must release its capacity slot.
        response = client.post("/api/v1/runs", json={"scenario_id": "healthy-baseline"})
        assert response.status_code == status
        assert response.json() == {"detail": {"code": code}}
    assert not path.exists()


def test_storage_failure_is_sanitized(tmp_path, monkeypatch):
    def fail(self, result):
        raise sqlite3.OperationalError("private filesystem detail")
    monkeypatch.setattr(api_module.RunStore, "save", fail)
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    response = client.post("/api/v1/runs", json={"scenario_id": "healthy-baseline"})
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "STORAGE_UNAVAILABLE"}}


def test_capacity_is_bounded(tmp_path, monkeypatch):
    entered = [Event(), Event()]
    release = Event()
    calls = []

    async def block(config):
        index = len(calls)
        calls.append(config)
        entered[index].set()
        assert release.wait(5)
        raise RunnerError("TIMEOUT")

    monkeypatch.setattr(api_module, "run_simulation", block)
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(client.post, "/api/v1/runs", json={"scenario_id": "healthy-baseline"})
        assert entered[0].wait(5)
        second = pool.submit(client.post, "/api/v1/runs", json={"scenario_id": "healthy-baseline"})
        try:
            assert entered[1].wait(5)
            response = client.post("/api/v1/runs", json={"scenario_id": "healthy-baseline"})
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "RUN_CAPACITY"
        finally:
            release.set()
        assert first.result().status_code == second.result().status_code == 504
