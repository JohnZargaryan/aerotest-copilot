import json

import pytest
from test_baseline import run

from aerotest.contracts import EventRecord


@pytest.mark.parametrize("seed", [0, 42, 4294967295])
def test_disagreement_schedule_evidence_and_replay(seed):
    config = {"scenario_id": "sensor-disagreement", "seed": seed, "duration_ms": 5000}
    result = run(config)
    assert result.returncode == 0
    assert result.stdout == run(config).stdout
    body = json.loads(result.stdout)
    records = [EventRecord.model_validate(r) for r in body["records"]]
    assert [r.sequence for r in records] == list(range(len(records)))
    assert len({r.event_id for r in records}) == len(records)
    transitions = [(r.sim_time_ms, r.state) for r in records if r.event_code == "STATE_TRANSITION"]
    assert transitions == [(0, "STARTUP"), (1000, "NOMINAL"),
                           (2500, "DEGRADED"), (5000, "SHUTDOWN")]
    baseline = json.loads(run({**config, "scenario_id": "healthy-baseline"}).stdout)
    samples = {(r.sim_time_ms, r.component_id): r for r in records if r.unit != "none"}
    for original in baseline["records"]:
        if original["unit"] == "none":
            continue
        time = original["sim_time_ms"]
        component = original["component_id"]
        sample = samples[time, component]
        bias = 6000 if component == "sensor-b" and 2000 <= time < 4000 else 0
        assert sample.measurement == original["measurement"] + bias
        assert sample.details["sample_time_ms"] == time
        if time >= 2500:
            assert sample.state == "DEGRADED"


@pytest.mark.parametrize("duration", [1000, 2000, 2400, 2500, 2600])
def test_short_runs_and_shutdown_precedence(duration):
    result = run({"scenario_id": "sensor-disagreement", "duration_ms": duration})
    assert result.returncode == 0
    records = json.loads(result.stdout)["records"]
    degraded = [r for r in records if r["state"] == "DEGRADED"]
    assert bool(degraded) == (duration > 2500)
    assert records[-1]["state"] == "SHUTDOWN"
    assert records[-1]["sim_time_ms"] == duration
