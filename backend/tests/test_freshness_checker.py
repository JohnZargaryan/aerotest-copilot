import asyncio

import pytest

from aerotest.checkers import check_freshness_response
from aerotest.contracts import SimulationConfig
from aerotest.runner import run_simulation


@pytest.fixture
def trace():
    return asyncio.run(run_simulation(SimulationConfig(scenario_id="missing-messages")))


def test_actual_delayed_messages_and_boundary(trace):
    check = check_freshness_response(trace)
    assert check.status == "PASS"
    assert check.requirement_id == "AT-REQ-002"
    assert set(check.evidence_ids) <= {r.event_id for r in trace.records}
    # Last ordinary sensor-b acquisition is 1900: 2200 is still fresh.
    assert all(r.state == "NOMINAL" for r in trace.records if r.sim_time_ms == 2200)


@pytest.mark.parametrize("time,state", [(2300, "NOMINAL"), (2400, "NOMINAL"),
                                       (3300, "DEGRADED"), (4000, "NOMINAL")])
def test_late_responses_and_recovery_fail(trace, time, state):
    for record in trace.records:
        if record.sim_time_ms == time:
            record.state = state
    check = check_freshness_response(trace)
    assert check.status == "FAIL"
    assert any(r.event_id in check.evidence_ids for r in trace.records if r.sim_time_ms == time)


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement"])
def test_fresh_runs_are_unexercised(scenario):
    trace = asyncio.run(run_simulation(SimulationConfig(scenario_id=scenario)))
    assert check_freshness_response(trace).status == "INCONCLUSIVE"


def test_future_acquisition_is_inconclusive(trace):
    trace.records[1].details["sample_time_ms"] = 100
    assert check_freshness_response(trace).status == "INCONCLUSIVE"


def test_missing_state_witness_is_inconclusive(trace):
    trace.records = [r for r in trace.records if not (
        r.component_id == "battery" and r.sim_time_ms == 2300)]
    for sequence, record in enumerate(trace.records):
        record.sequence = sequence
        record.event_id = f"{trace.run_id}-e{sequence}"
    assert check_freshness_response(trace).status == "INCONCLUSIVE"
