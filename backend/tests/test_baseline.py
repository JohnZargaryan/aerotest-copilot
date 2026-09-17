import json
import os
import subprocess
from pathlib import Path

import pytest

from aerotest.contracts import EventRecord, SimulationConfig

ROOT = Path(__file__).resolve().parents[2]


def run(config):
    name = "aerotest-sim.exe" if os.name == "nt" else "aerotest-sim"
    binary = Path(os.environ.get("AEROTEST_SIM", ROOT / "build" / name))
    return subprocess.run(
        [str(binary), "--run"], input=json.dumps(config).encode(),
        capture_output=True, timeout=5, check=False,
    )


@pytest.mark.parametrize("duration", [1000, 1100, 30000, 120000])
def test_baseline_matches_event_contract_and_timing(duration):
    result = run({"scenario_id": "healthy-baseline", "duration_ms": duration})
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout.endswith(b"\n") and b"\r" not in result.stdout
    body = json.loads(result.stdout)
    assert body["schema_version"] == "1.0"
    assert body["simulator_version"] == "0.3.0"
    assert body["status"] == "completed"
    SimulationConfig.model_validate(body["config"])
    records = [EventRecord.model_validate(item) for item in body["records"]]
    assert len({r.event_id for r in records}) == len(records)
    assert [r.sequence for r in records] == list(range(len(records)))
    assert all(r.run_id == body["run_id"] and r.severity == "INFO" for r in records)
    transitions = [(r.sim_time_ms, r.state) for r in records if r.unit == "none"]
    expected = [(0, "STARTUP")]
    if duration > 1000:
        expected.append((1000, "NOMINAL"))
    assert transitions == expected + [(duration, "SHUTDOWN")]
    for component in ("sensor-a", "sensor-b", "battery"):
        samples = [r for r in records if r.component_id == component]
        assert [r.sim_time_ms for r in samples] == list(range(0, duration, 100))
        assert all(r.details["sample_time_ms"] == r.sim_time_ms for r in samples)
        assert all(r.state == ("STARTUP" if r.sim_time_ms < 1000 else "NOMINAL") for r in samples)
        if component == "battery":
            assert all(r.unit == "basis_points" for r in samples)
            assert [r.measurement for r in samples] == [10000 - i for i in range(duration // 100)]
        else:
            assert all(r.unit == "mdegC" and 19900 <= r.measurement <= 20100 for r in samples)
    assert len(result.stdout) < 2_000_000


def test_replay_normalizes_defaults_and_ignores_json_key_order():
    minimal = run({"scenario_id": "healthy-baseline"})
    explicit = run({"step_ms": 100, "seed": 42, "duration_ms": 30000,
                    "scenario_id": "healthy-baseline", "schema_version": "1.0"})
    assert minimal.returncode == explicit.returncode == 0
    assert minimal.stdout == explicit.stdout
    assert minimal.stdout == run({"scenario_id": "healthy-baseline"}).stdout


def test_seed_changes_measurements_and_identity():
    a = json.loads(run({"scenario_id": "healthy-baseline", "seed": 42}).stdout)
    b = json.loads(run({"scenario_id": "healthy-baseline", "seed": 43}).stdout)
    assert a["run_id"] != b["run_id"]
    assert a["records"][1]["measurement"] != b["records"][1]["measurement"]


@pytest.mark.parametrize(
    "scenario", ["missing-messages", "battery-degradation"]
)
def test_planned_fault_scenarios_do_not_silently_run_baseline(scenario):
    result = run({"scenario_id": scenario})
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["code"] == "SCENARIO_NOT_IMPLEMENTED"


def test_run_rejects_invalid_duration_before_simulating():
    result = run({"scenario_id": "healthy-baseline", "duration_ms": 1050})
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_CONFIG"


def test_canonical_output_matches_cross_platform_snapshot():
    import hashlib

    result = run({"scenario_id": "healthy-baseline", "duration_ms": 1000})
    assert result.returncode == 0
    assert hashlib.sha256(result.stdout).hexdigest() == (
        "66337f3bd6db934d02adafd50ffb1a54c0b99ee5aa71d64c43e473014ba8deaa"
    )
