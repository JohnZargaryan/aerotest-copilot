from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aerotest.app import create_app


@pytest.mark.parametrize("scenario,exercised", [("healthy-baseline", None),
                                              ("sensor-disagreement", "AT-REQ-001"),
                                              ("missing-messages", "AT-REQ-002"),
                                              ("battery-degradation", "AT-REQ-003")])
def test_saved_run_report_is_scoped_repeatable_and_read_only(tmp_path, scenario, exercised):
    path = tmp_path / "runs.sqlite"
    with TestClient(create_app(path)) as client:
        created = client.post("/api/v1/runs", json={"scenario_id": scenario})
        assert created.status_code == 201
        location = created.headers["Location"]
        original = created.json()
    with TestClient(create_app(path)) as client:
        response = client.get(location + "/checks")
        assert response.status_code == 200
        body = response.json()
        assert body == client.get(location + "/checks").json()
        assert original == client.get(location).json()
    assert body["execution_id"] == original["execution_id"]
    assert body["run_id"] == original["result"]["run_id"]
    assert body["unassessed_requirements"] == ["AT-REQ-004", "AT-REQ-005"]
    assert "overall_status" not in body
    checks = {c["requirement_id"]: c for c in body["checks"]}
    assert len(checks) == 4
    ids = {r["event_id"] for r in original["result"]["records"]}
    for requirement, check in checks.items():
        expected = "PASS" if requirement in (exercised, "AT-REQ-006") else "INCONCLUSIVE"
        assert check["status"] == expected
        assert check["scope"]
        assert set(check["evidence_ids"]) <= ids


def test_report_missing_and_invalid_ids(tmp_path):
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    assert client.get(f"/api/v1/runs/{uuid4()}/checks").status_code == 404
    assert client.get("/api/v1/runs/bad/checks").status_code == 422


def test_report_in_openapi(tmp_path):
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    schema = client.get("/openapi.json").json()
    assert "/api/v1/runs/{execution_id}/checks" in schema["paths"]
    assert "CheckReport" in schema["components"]["schemas"]
