import json

import pytest
from test_baseline import run

from aerotest.contracts import EventRecord


@pytest.mark.parametrize("seed", [0, 42, 4294967295])
def test_missing_and_delayed_evidence_and_replay(seed):
    config = {"scenario_id": "missing-messages", "seed": seed, "duration_ms": 5000}
    result = run(config)
    assert result.returncode == 0
    assert result.stdout == run(config).stdout
    records = [EventRecord.model_validate(r) for r in json.loads(result.stdout)["records"]]
    transitions = [(r.sim_time_ms, r.state) for r in records if r.unit == "none"]
    assert transitions == [(0, "STARTUP"), (1000, "NOMINAL"), (2300, "DEGRADED"),
                           (3300, "SAFE"), (5000, "SHUTDOWN")]
    assert [r.sequence for r in records] == list(range(len(records)))
    assert len({r.event_id for r in records}) == len(records)
    baseline = json.loads(run({**config, "scenario_id": "healthy-baseline"}).stdout)
    expected = {(r["sim_time_ms"], r["component_id"]): r["measurement"]
                for r in baseline["records"] if r["unit"] != "none"}
    for component, start in [("sensor-a", 3000), ("sensor-b", 2000)]:
        samples = [r for r in records if r.component_id == component]
        times = [t for t in range(0, 5000, 100) if not start <= t < 4000]
        if component == "sensor-b":
            times = sorted(times + [2400])
        assert [r.sim_time_ms for r in samples] == times
        for sample in samples:
            acquired = 2000 if component == "sensor-b" and sample.sim_time_ms == 2400 else (
                sample.sim_time_ms
            )
            assert sample.details["sample_time_ms"] == acquired
            assert sample.measurement == expected[acquired, component]
            if sample.sim_time_ms >= 4000:
                assert sample.state == "SAFE"


@pytest.mark.parametrize("duration", [1000, 2300, 2400, 3300, 3400])
def test_shutdown_and_freshness_boundaries(duration):
    result = run({"scenario_id": "missing-messages", "duration_ms": duration})
    assert result.returncode == 0
    records = json.loads(result.stdout)["records"]
    assert any(r["state"] == "DEGRADED" for r in records) == (duration > 2300)
    assert any(r["state"] == "SAFE" for r in records) == (duration > 3300)
    assert records[-1]["state"] == "SHUTDOWN"
    assert records[-1]["sim_time_ms"] == duration
