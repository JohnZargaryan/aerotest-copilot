import asyncio

import pytest

from aerotest.checkers import check_disagreement_response
from aerotest.contracts import SimulationConfig
from aerotest.runner import run_simulation


@pytest.fixture
def trace():
    return asyncio.run(run_simulation(SimulationConfig(scenario_id="sensor-disagreement")))


def test_real_trace_and_citations(trace):
    check = check_disagreement_response(trace)
    assert check.status == "PASS"
    assert check.requirement_id == "AT-REQ-001"
    assert set(check.evidence_ids) <= {r.event_id for r in trace.records}


def test_first_eligible_tick_failure(trace):
    for record in trace.records:
        if record.sim_time_ms == 2500:
            record.state = "NOMINAL"
    check = check_disagreement_response(trace)
    assert check.status == "FAIL"
    assert "2500" in check.reason


@pytest.mark.parametrize("difference,status", [(5000, "INCONCLUSIVE"),
                                              (5001, "PASS"), (-5001, "PASS")])
def test_strict_difference_threshold(trace, difference, status):
    for record in trace.records:
        if record.event_code == "SENSOR_SAMPLE":
            record.measurement = 20000 + (difference if record.component_id == "sensor-b"
                                         and 2000 <= record.sim_time_ms < 4000 else 0)
    assert check_disagreement_response(trace).status == status


def test_agreement_resets_timer(trace):
    for record in trace.records:
        if record.sim_time_ms == 2400 and record.event_code == "SENSOR_SAMPLE":
            record.measurement = 20000
        if record.sim_time_ms == 2500:
            record.state = "NOMINAL"
    assert check_disagreement_response(trace).status == "PASS"


def test_staleness_resets_timer(trace):
    trace.records = [r for r in trace.records if not (
        r.component_id == "sensor-b" and 2100 <= r.sim_time_ms <= 2500)]
    for index, record in enumerate(trace.records):
        record.sequence = index
        record.event_id = f"{trace.run_id}-e{index}"
        if record.sim_time_ms == 2500:
            record.state = "NOMINAL"
    assert check_disagreement_response(trace).status == "PASS"


@pytest.mark.parametrize("duration", [2400, 2500])
def test_shutdown_before_detection_is_unexercised(duration):
    trace = asyncio.run(run_simulation(
        SimulationConfig(scenario_id="sensor-disagreement", duration_ms=duration)))
    assert check_disagreement_response(trace).status == "INCONCLUSIVE"


def test_missing_initial_sensor_is_inconclusive(trace):
    trace.records[1].component_id = "other"
    assert check_disagreement_response(trace).status == "INCONCLUSIVE"
