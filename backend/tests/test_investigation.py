import asyncio
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from aerotest.contracts import SimulationConfig
from aerotest.investigation import CitationQuery, EventQuery, EvidenceTools
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
