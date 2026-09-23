import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from aerotest.app import app
from aerotest.contracts import SimulationConfig

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "contracts/config-cases.json").read_text())
client = TestClient(app)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_config_contract_and_api(case):
    response = client.post("/api/v1/config/validate", json=case["input"])
    if case["valid"]:
        expected = SimulationConfig.model_validate(case["input"]).model_dump()
        assert response.status_code == 200
        assert response.json() == expected
    else:
        with pytest.raises(ValidationError):
            SimulationConfig.model_validate(case["input"])
        assert response.status_code == 422


def test_health_does_not_claim_future_capabilities():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["simulation_available"] is True
    assert response.json()["investigation_available"] is False


def test_malformed_json_is_rejected():
    response = client.post(
        "/api/v1/config/validate", content="{", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
