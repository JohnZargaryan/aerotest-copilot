import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aerotest.adapters import LiveModeDisabled, create_investigator
from aerotest.app import create_app
from aerotest.assistant import InvestigationRequest, ScriptedInvestigator
from aerotest.storage import RunStore


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                      "missing-messages", "battery-degradation"])
def test_api_matches_local_assistant_and_preserves_storage(tmp_path, scenario):
    path = tmp_path / "runs.sqlite"
    client = TestClient(create_app(path))
    saved = client.post("/api/v1/runs", json={"scenario_id": scenario}).json()
    identifier = saved["execution_id"]
    url = f"/api/v1/runs/{identifier}/investigation"
    response = client.get(url)
    assert response.status_code == 200
    expected = ScriptedInvestigator(RunStore(path)).investigate(
        InvestigationRequest(execution_id=identifier))
    assert response.json() == expected.model_dump(mode="json")
    assert TestClient(create_app(path)).get(url).json() == response.json()
    assert client.get(f"/api/v1/runs/{identifier}").json() == saved
    selected = client.get(url, params={"requirement_id": "AT-REQ-001"}).json()
    assert [f["requirement_id"] for f in selected["findings"]] == ["AT-REQ-001"]
    assert client.get("/api/v1/health").json()["investigation_available"] is True


@pytest.mark.parametrize("suffix", ["not-a-uuid/investigation",
                                     str(uuid4()) + "/investigation?mode=unknown",
                                     str(uuid4()) + "/investigation?requirement_id=AT-REQ-004"])
def test_invalid_api_arguments(tmp_path, suffix):
    response = TestClient(create_app(tmp_path / "runs.sqlite")).get("/api/v1/runs/" + suffix)
    assert response.status_code == 422


def test_missing_execution_and_openapi(tmp_path):
    client = TestClient(create_app(tmp_path / "runs.sqlite"))
    response = client.get(f"/api/v1/runs/{uuid4()}/investigation")
    assert response.status_code == 404 and response.json()["detail"]["code"] == "RUN_NOT_FOUND"
    schema = client.get("/openapi.json").json()
    assert "/api/v1/runs/{execution_id}/investigation" in schema["paths"]
    assert "ScriptedInvestigation" in schema["components"]["schemas"]


def test_disabled_live_mode_never_reads_storage(tmp_path, monkeypatch):
    def forbidden(*args):
        raise AssertionError("disabled live mode accessed storage")
    monkeypatch.setattr(RunStore, "get", forbidden)
    store = RunStore(tmp_path / "runs.sqlite")
    with pytest.raises(LiveModeDisabled):
        create_investigator(store, "live")
    with pytest.raises(ValueError, match="UNSUPPORTED_ASSISTANT_MODE"):
        create_investigator(store, "unknown")
    response = TestClient(create_app(tmp_path / "runs.sqlite")).get(
        f"/api/v1/runs/{uuid4()}/investigation?mode=live")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "LIVE_MODE_DISABLED"


@pytest.mark.parametrize("error,status,code", [
    (sqlite3.OperationalError("private path"), 503, "STORAGE_UNAVAILABLE"),
    (LookupError("CITATION_NOT_FOUND"), 500, "INVESTIGATION_INVALID"),
    (ValueError("private detail"), 500, "INVESTIGATION_INVALID")])
def test_clean_failure_responses(tmp_path, monkeypatch, error, status, code):
    class BrokenInvestigator:
        def investigate(self, request):
            raise error
    monkeypatch.setattr("aerotest.app.create_investigator", lambda *_: BrokenInvestigator())
    response = TestClient(create_app(tmp_path / "runs.sqlite")).get(
        f"/api/v1/runs/{uuid4()}/investigation")
    assert response.status_code == status
    assert response.json() == {"detail": {"code": code}}
