import json

import pytest
from test_baseline import run

from aerotest.contracts import EventRecord


@pytest.mark.parametrize("seed", [0, 42, 4294967295])
def test_battery_telemetry_transitions_and_replay(seed):
    config = {"scenario_id": "battery-degradation", "seed": seed, "duration_ms": 120000}
    result = run(config)
    assert result.returncode == 0
    assert result.stdout == run(config).stdout
    records = [EventRecord.model_validate(r) for r in json.loads(result.stdout)["records"]]
    transitions = [(r.sim_time_ms, r.state) for r in records if r.unit == "none"]
    assert transitions == [(0, "STARTUP"), (1000, "NOMINAL"), (8100, "DEGRADED"),
                           (9100, "SAFE"), (120000, "SHUTDOWN")]
    assert [r.sequence for r in records] == list(range(len(records)))
    assert len({r.event_id for r in records}) == len(records)
    battery = [r for r in records if r.component_id == "battery"]
    assert [r.sim_time_ms for r in battery] == list(range(0, 120000, 100))
    assert [r.measurement for r in battery] == [max(0, 10000 - i * 100) for i in range(1200)]
    assert all(r.unit == "basis_points" for r in battery)
    assert all(r.state == "SAFE" for r in battery if r.sim_time_ms >= 9100)
    baseline = json.loads(run({**config, "scenario_id": "healthy-baseline"}).stdout)
    actual = [(r.sim_time_ms, r.component_id, r.measurement, r.details)
              for r in records if r.event_code == "SENSOR_SAMPLE"]
    expected = [(r["sim_time_ms"], r["component_id"], r["measurement"], r["details"])
                for r in baseline["records"] if r["event_code"] == "SENSOR_SAMPLE"]
    assert actual == expected


@pytest.mark.parametrize("duration", [1000, 8000, 8100, 8200, 9000, 9100, 9200])
def test_battery_boundaries_and_shutdown(duration):
    result = run({"scenario_id": "battery-degradation", "duration_ms": duration})
    assert result.returncode == 0
    records = json.loads(result.stdout)["records"]
    assert any(r["state"] == "DEGRADED" for r in records) == (duration > 8100)
    assert any(r["state"] == "SAFE" for r in records) == (duration > 9100)
    assert records[-1]["state"] == "SHUTDOWN"
    assert records[-1]["sim_time_ms"] == duration
