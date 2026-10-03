import asyncio
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from aerotest.contracts import SimulationConfig
from aerotest.investigation import CitationQuery, ComparisonQuery, EventQuery, EvidenceTools
from aerotest.reports import build_report
from aerotest.runner import run_simulation
from aerotest.storage import RunStore


@pytest.fixture
def evidence(tmp_path):
    store = RunStore(tmp_path / "runs.sqlite")
    saved = store.save(asyncio.run(run_simulation(
        SimulationConfig(scenario_id="sensor-disagreement"))))
    return store, saved, EvidenceTools(store)


def test_page_limits_order_and_no_omissions(evidence):
    store, saved, tools = evidence
    collected = []
    offset = 0
    while True:
        page = tools.query_events(EventQuery(execution_id=saved.execution_id,
                                            offset=offset, limit=100))
        assert len(page.events) <= 100
        collected.extend(page.events)
        if page.next_offset is None:
            break
        offset = page.next_offset
    assert collected == saved.result.records
    assert store.get(saved.execution_id) == saved


def test_combined_filters_include_interval_boundaries(evidence):
    _, saved, tools = evidence
    page = tools.query_events(EventQuery(execution_id=saved.execution_id, start_ms=2500,
                                        end_ms=2600, component_id="sensor-b",
                                        state="DEGRADED", event_code="SENSOR_SAMPLE"))
    assert [r.sim_time_ms for r in page.events] == [2500, 2600]
    assert page.total_matches == 2 and page.next_offset is None


def test_report_citations_resolve_in_requested_order(evidence):
    _, saved, tools = evidence
    ids = build_report(saved).checks[0].evidence_ids[:20]
    events = tools.resolve_citations(CitationQuery(execution_id=saved.execution_id,
                                                  event_ids=list(reversed(ids))))
    assert [r.event_id for r in events] == list(reversed(ids))


@pytest.mark.parametrize("arguments", [{"limit": 101}, {"limit": True}, {"offset": -1},
                                      {"start_ms": 200, "end_ms": 100},
                                      {"component_id": "'; DROP TABLE executions"},
                                      {"sql": "SELECT *"}])
def test_invalid_queries_rejected(arguments):
    with pytest.raises(ValidationError):
        EventQuery(execution_id=uuid4(), **arguments)


def test_missing_execution_and_citation(evidence):
    _, saved, tools = evidence
    with pytest.raises(LookupError, match="EXECUTION_NOT_FOUND"):
        tools.query_events(EventQuery(execution_id=uuid4()))
    with pytest.raises(LookupError, match="CITATION_NOT_FOUND"):
        tools.resolve_citations(CitationQuery(execution_id=saved.execution_id,
                                              event_ids=["wrong-run-e1"]))


def test_duplicate_and_excessive_citations_rejected():
    for ids in [["a", "a"], [str(i) for i in range(21)]]:
        with pytest.raises(ValidationError):
            CitationQuery(execution_id=uuid4(), event_ids=ids)


def test_bypassed_query_is_revalidated(evidence):
    _, saved, tools = evidence
    query = EventQuery.model_construct(execution_id=UUID(saved.execution_id), limit=10000)
    with pytest.raises(ValidationError):
        tools.query_events(query)


@pytest.fixture
def comparisons(evidence):
    store, fault, tools = evidence
    baseline = store.save(asyncio.run(run_simulation(
        SimulationConfig(scenario_id="healthy-baseline"))))
    return store, baseline, fault, tools


def test_comparison_matches_ticks_despite_shifted_sequences(comparisons):
    store, baseline, fault, tools = comparisons
    query = ComparisonQuery(left_execution_id=baseline.execution_id,
                            right_execution_id=fault.execution_id, limit=100)
    differences = []
    while True:
        page = tools.compare_runs(query)
        assert len(page.differences) <= 100
        differences.extend(page.differences)
        if page.next_offset is None:
            break
        query.offset = page.next_offset
    assert len(differences) == page.total_differences
    biased = [d for d in differences if d.right and d.right.component_id == "sensor-b"
              and 2000 <= d.right.sim_time_ms < 4000]
    assert len(biased) == 20
    assert all(d.measurement_delta == 6000 for d in biased)
    assert any(d.left is None and d.right.event_code == "STATE_TRANSITION" for d in differences)
    for d in biased:
        assert tools.resolve_citations(CitationQuery(execution_id=baseline.execution_id,
                                                    event_ids=[d.left.event_id])) == [d.left]
        assert tools.resolve_citations(CitationQuery(execution_id=fault.execution_id,
                                                    event_ids=[d.right.event_id])) == [d.right]
    reverse = tools.compare_runs(ComparisonQuery(left_execution_id=fault.execution_id,
                                                 right_execution_id=baseline.execution_id,
                                                 limit=100))
    assert any(d.measurement_delta == -6000 for d in reverse.differences)
    assert store.get(baseline.execution_id) == baseline
    assert store.get(fault.execution_id) == fault


def test_replay_has_no_content_differences(evidence):
    store, saved, tools = evidence
    replay = store.save(saved.result)
    page = tools.compare_runs(ComparisonQuery(left_execution_id=saved.execution_id,
                                             right_execution_id=replay.execution_id))
    assert page.total_differences == 0 and page.differences == []
    assert page.next_offset is None


def test_missing_delivery_and_shorter_duration(comparisons):
    store, baseline, _, tools = comparisons
    missing = store.save(asyncio.run(run_simulation(
        SimulationConfig(scenario_id="missing-messages", duration_ms=4000))))
    query = ComparisonQuery(left_execution_id=baseline.execution_id,
                            right_execution_id=missing.execution_id, limit=100)
    page = tools.compare_runs(query)
    assert page.left_config.duration_ms == 30000 and page.right_config.duration_ms == 4000
    assert any(d.left and d.left.component_id == "sensor-b" and d.left.sim_time_ms == 2000
               and d.right is None for d in page.differences)
    query.offset = page.next_offset
    page = tools.compare_runs(query)
    assert any(d.left and d.left.sim_time_ms > 4000 and d.right is None
               for d in page.differences)


@pytest.mark.parametrize("arguments", [{"limit": 101}, {"limit": True}, {"offset": 8001},
                                      {"offset": -1}, {"command": "run"}])
def test_invalid_comparison_arguments(arguments):
    with pytest.raises(ValidationError):
        ComparisonQuery(left_execution_id=uuid4(), right_execution_id=uuid4(), **arguments)


def test_comparison_missing_execution_and_bypass(evidence):
    _, saved, tools = evidence
    with pytest.raises(LookupError, match="EXECUTION_NOT_FOUND"):
        tools.compare_runs(ComparisonQuery(left_execution_id=saved.execution_id,
                                            right_execution_id=uuid4()))
    with pytest.raises(ValidationError):
        tools.compare_runs(ComparisonQuery.model_construct(
            left_execution_id=UUID(saved.execution_id),
            right_execution_id=UUID(saved.execution_id), limit=1000))
