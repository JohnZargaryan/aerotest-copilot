import asyncio

import pytest

from aerotest.checkers import check_transition_edges
from aerotest.contracts import SimulationConfig
from aerotest.runner import run_simulation


@pytest.fixture
def trace():
    return asyncio.run(run_simulation(SimulationConfig(scenario_id="battery-degradation")))


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                      "missing-messages", "battery-degradation"])
def test_real_transition_policy_and_resolvable_citations(scenario):
    trace = asyncio.run(run_simulation(SimulationConfig(scenario_id=scenario)))
    check = check_transition_edges(trace)
    assert check.status == "PASS"
    assert check.requirement_id == "AT-REQ-006"
    ids = {r.event_id for r in trace.records}
    assert check.evidence_ids and set(check.evidence_ids) <= ids


@pytest.mark.parametrize("mutation", ["recovery", "disconnected", "destination", "sample"])
def test_defective_trace_is_detected(trace, mutation):
    event = next(r for r in trace.records if r.state == "SAFE")
    if mutation == "recovery":
        event = trace.records[-1]
        event.details["to_state"] = "NOMINAL"
    elif mutation == "disconnected":
        event.details["from_state"] = "OFF"
    elif mutation == "destination":
        event.state = "NOMINAL"
    else:
        event = trace.records[1]
        event.state = "SAFE"
    check = check_transition_edges(trace)
    assert check.status == "FAIL"
    assert event.event_id in check.evidence_ids


def test_missing_evidence_is_inconclusive(trace):
    trace.records.pop()
    assert check_transition_edges(trace).status == "INCONCLUSIVE"


def test_missing_endpoints_are_inconclusive(trace):
    trace.records[0].details.clear()
    assert check_transition_edges(trace).status == "INCONCLUSIVE"


def test_minimum_duration_startup_shutdown_is_valid():
    trace = asyncio.run(run_simulation(
        SimulationConfig(scenario_id="healthy-baseline", duration_ms=1000)))
    assert check_transition_edges(trace).status == "PASS"
