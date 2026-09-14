"""Real subprocess contract tests, not a replacement for the future bounded runner."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from aerotest.contracts import SimulationConfig

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "contracts/config-cases.json").read_text())


@pytest.fixture(scope="module")
def binary():
    name = "aerotest-sim.exe" if os.name == "nt" else "aerotest-sim"
    path = Path(os.environ.get("AEROTEST_SIM", ROOT / "build" / name))
    if not path.is_file():
        pytest.fail(f"Build the C++ target before integration tests: {path}")
    return path


def execute(binary, payload):
    return subprocess.run(
        [str(binary), "--validate-config"],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_python_and_cpp_agree(binary, case):
    result = execute(binary, json.dumps(case["input"]))
    response = json.loads(result.stdout)
    assert result.stderr == ""
    if case["valid"]:
        assert result.returncode == 0
        assert response["config"] == SimulationConfig.model_validate(case["input"]).model_dump()
    else:
        assert result.returncode == 2
        assert response["status"] == "error"
        assert response["error"]["code"] == "INVALID_CONFIG"


@pytest.mark.parametrize(
    "payload", ["{", "", " " * 65537], ids=["malformed", "empty", "over-size-limit"]
)
def test_bad_input_returns_structured_error(binary, payload):
    result = execute(binary, payload)
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_CONFIG"


def test_normalized_config_is_reproducible(binary):
    payload = '{"scenario_id":"healthy-baseline"}'
    assert execute(binary, payload).stdout == execute(binary, payload).stdout
