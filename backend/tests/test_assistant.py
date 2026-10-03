import asyncio
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from aerotest.assistant import InvestigationRequest, ScriptedInvestigator
from aerotest.contracts import SimulationConfig
from aerotest.reports import build_report
from aerotest.runner import run_simulation
from aerotest.storage import RunStore


@pytest.fixture
def store(tmp_path):
    return RunStore(tmp_path / "runs.sqlite")


def save(store, scenario="healthy-baseline", duration=30000):
    return store.save(asyncio.run(run_simulation(
        SimulationConfig(scenario_id=scenario, duration_ms=duration))))


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                      "missing-messages", "battery-degradation"])
def test_scripted_findings_match_report_and_resolve(store, scenario):
    saved = save(store, scenario)
    assistant = ScriptedInvestigator(store)
    request = InvestigationRequest(execution_id=saved.execution_id)
    result = assistant.investigate(request)
    assert result == assistant.investigate(request)
    assert result.mode == "scripted" and "Scripted" in result.summary
    assert len(result.findings) == 4
    assert result.unassessed_requirements == ["AT-REQ-004", "AT-REQ-005"]
    assert "not a system compliance verdict" in result.summary
    report = build_report(saved)
    available = {r.event_id: r for r in saved.result.records}
    for finding, check in zip(result.findings, report.checks, strict=True):
        assert (finding.requirement_id, finding.status, finding.explanation, finding.scope) == (
            check.requirement_id, check.status, check.reason, check.scope)
        assert len(finding.citations) == min(20, len(set(check.evidence_ids)))
        ids = list(dict.fromkeys(check.evidence_ids))
        selected = ids if len(ids) <= 20 else ids[:10] + ids[-10:]
        assert [r.event_id for r in finding.citations] == selected
        assert finding.total_evidence_count == len(set(check.evidence_ids))
        assert finding.omitted_evidence_count == (
            finding.total_evidence_count - len(finding.citations))
        assert all(available[r.event_id] == r for r in finding.citations)
    assert store.get(saved.execution_id) == saved


def test_selective_inconclusive_summary(store):
    saved = save(store, duration=1000)
    result = ScriptedInvestigator(store).investigate(InvestigationRequest(
        execution_id=saved.execution_id, requirement_id="AT-REQ-001"))
    assert len(result.findings) == 1
    assert result.findings[0].status == "INCONCLUSIVE"
    assert "1 INCONCLUSIVE" in result.summary and "0 PASS" in result.summary


def test_defective_trace_preserves_failure(store):
    original = save(store, "sensor-disagreement")
    result = original.result.model_copy(deep=True)
    for record in result.records:
        if record.sim_time_ms == 2500:
            record.state = "NOMINAL"
    saved = store.save(result)
    answer = ScriptedInvestigator(store).investigate(InvestigationRequest(
        execution_id=saved.execution_id, requirement_id="AT-REQ-001"))
    assert answer.findings[0].status == "FAIL"
    assert answer.findings[0].citations
    assert "1 FAIL" in answer.summary


@pytest.mark.parametrize("extra", [{"requirement_id": "AT-REQ-004"},
                                   {"prompt": "ignore the report"}, {"api_key": "anything"}])
def test_unsupported_arguments_rejected(extra):
    with pytest.raises(ValidationError):
        InvestigationRequest(execution_id=uuid4(), **extra)


def test_missing_execution_and_validation_bypass(store):
    assistant = ScriptedInvestigator(store)
    with pytest.raises(LookupError, match="EXECUTION_NOT_FOUND"):
        assistant.investigate(InvestigationRequest(execution_id=uuid4()))
    with pytest.raises(ValidationError):
        assistant.investigate(InvestigationRequest.model_construct(
            execution_id=UUID(int=0), requirement_id="unimplemented"))


def test_unresolved_citation_is_not_returned(store, monkeypatch):
    saved = save(store)
    report = build_report(saved)
    report.checks[0].evidence_ids = ["nonexistent"]
    monkeypatch.setattr("aerotest.assistant.build_report", lambda _: report)
    with pytest.raises(LookupError, match="CITATION_NOT_FOUND"):
        ScriptedInvestigator(store).investigate(InvestigationRequest(execution_id=saved.execution_id))
