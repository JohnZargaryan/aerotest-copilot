import asyncio

import pytest

from aerotest.checkers import check_battery_response
from aerotest.contracts import SimulationConfig
from aerotest.runner import run_simulation


@pytest.fixture
def trace():
    return asyncio.run(run_simulation(SimulationConfig(scenario_id="battery-degradation")))


def test_real_battery_response_and_citations(trace):
    check = check_battery_response(trace)
    assert check.status == "PASS"
    assert check.requirement_id == "AT-REQ-003"
    assert set(check.evidence_ids) <= {r.event_id for r in trace.records}


@pytest.mark.parametrize("time,state", [(8100, "NOMINAL"), (9100, "DEGRADED"),
                                       (11000, "NOMINAL")])
def test_late_response_and_unlatched_safe_fail(trace, time, state):
    record = next(r for r in trace.records if r.component_id == "battery" and r.sim_time_ms == time)
    record.state = state
    check = check_battery_response(trace)
    assert check.status == "FAIL"
    assert record.event_id in check.evidence_ids


def test_exact_thresholds_do_not_require_stricter_state(trace):
    assert next(r for r in trace.records if r.component_id == "battery"
                and r.sim_time_ms == 8000).measurement == 2000
    assert next(r for r in trace.records if r.component_id == "battery"
                and r.sim_time_ms == 9000).measurement == 1000
    assert check_battery_response(trace).status == "PASS"


def test_safe_must_latch_after_power_recovers(trace):
    for record in trace.records:
        if record.component_id == "battery" and record.sim_time_ms >= 10000:
            record.measurement = 10000
    assert check_battery_response(trace).status == "PASS"
    next(r for r in trace.records if r.component_id == "battery"
         and r.sim_time_ms == 11000).state = "DEGRADED"
    assert check_battery_response(trace).status == "FAIL"


def test_missing_power_sample_is_inconclusive(trace):
    trace.records = [r for r in trace.records if not (
        r.component_id == "battery" and r.sim_time_ms == 8000)]
    for sequence, record in enumerate(trace.records):
        record.sequence = sequence
        record.event_id = f"{trace.run_id}-e{sequence}"
    assert check_battery_response(trace).status == "INCONCLUSIVE"


def test_unexercised_short_run_is_inconclusive():
    trace = asyncio.run(run_simulation(
        SimulationConfig(scenario_id="battery-degradation", duration_ms=8100)))
    assert check_battery_response(trace).status == "INCONCLUSIVE"


def test_wrong_unit_is_inconclusive(trace):
    next(r for r in trace.records if r.component_id == "battery").unit = "mdegC"
    assert check_battery_response(trace).status == "INCONCLUSIVE"
