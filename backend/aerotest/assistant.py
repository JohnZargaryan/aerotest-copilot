"""Deterministic report narration, explicitly labeled as scripted rather than an LLM."""

from typing import Literal
from uuid import UUID

from aerotest.contracts import Contract, EventRecord
from aerotest.investigation import CitationQuery, EvidenceTools
from aerotest.reports import build_report
from aerotest.storage import RunStore

RequirementId = Literal["AT-REQ-001", "AT-REQ-002", "AT-REQ-003", "AT-REQ-006"]


class InvestigationRequest(Contract):
    execution_id: UUID
    requirement_id: RequirementId | None = None


class InvestigationFinding(Contract):
    requirement_id: RequirementId
    status: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    explanation: str
    scope: str
    citations: list[EventRecord]
    total_evidence_count: int
    omitted_evidence_count: int


class ScriptedInvestigation(Contract):
    mode: Literal["scripted"] = "scripted"
    assistant_version: Literal["0.1.0"] = "0.1.0"
    checker_version: str
    execution_id: UUID
    run_id: str
    summary: str
    findings: list[InvestigationFinding]
    unassessed_requirements: list[str]
    scope: str
    tool_activity: list[str]


class ScriptedInvestigator:
    def __init__(self, store: RunStore):
        self.store = store
        self.tools = EvidenceTools(store)

    def investigate(self, request: InvestigationRequest) -> ScriptedInvestigation:
        request = InvestigationRequest.model_validate(request.model_dump())
        execution = self.store.get(str(request.execution_id))
        if execution is None:
            raise LookupError("EXECUTION_NOT_FOUND")
        report = build_report(execution)
        findings = []
        activity = ["build_report"]
        for check in report.checks:
            if (request.requirement_id is not None
                    and request.requirement_id != check.requirement_id):
                continue
            # Retain the beginning and end of long evidence chains; disclose omissions.
            ids = list(dict.fromkeys(check.evidence_ids))
            selected = ids if len(ids) <= 20 else ids[:10] + ids[-10:]
            citations = []
            if selected:
                citations = self.tools.resolve_citations(CitationQuery(
                    execution_id=request.execution_id, event_ids=selected))
                activity.append("resolve_citations:" + check.requirement_id)
            findings.append(InvestigationFinding(
                requirement_id=check.requirement_id, status=check.status,
                explanation=check.reason, scope=check.scope, citations=citations,
                total_evidence_count=len(ids), omitted_evidence_count=len(ids) - len(selected)))
        counts = {status: sum(f.status == status for f in findings)
                  for status in ("PASS", "FAIL", "INCONCLUSIVE")}
        summary = (f"Scripted check summary: {counts['PASS']} PASS, {counts['FAIL']} FAIL, "
                   f"{counts['INCONCLUSIVE']} INCONCLUSIVE in the selected checks. "
                   "These are scoped observations, not a system compliance verdict.")
        return ScriptedInvestigation(
            checker_version=report.checker_version, execution_id=request.execution_id,
            run_id=report.run_id, summary=summary, findings=findings,
            unassessed_requirements=report.unassessed_requirements,
            scope=report.scope, tool_activity=activity)
