"""Versioned, on-demand reports over saved evidence; no full-compliance verdict."""

from dataclasses import asdict
from typing import Literal

from aerotest.checkers import (
    check_battery_response,
    check_disagreement_response,
    check_freshness_response,
    check_transition_edges,
)
from aerotest.contracts import Contract
from aerotest.storage import StoredExecution


class RequirementCheck(Contract):
    requirement_id: str
    status: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    reason: str
    evidence_ids: list[str]
    scope: str


class CheckReport(Contract):
    schema_version: Literal["1.0"] = "1.0"
    checker_version: Literal["0.1.0"] = "0.1.0"
    execution_id: str
    run_id: str
    checks: list[RequirementCheck]
    unassessed_requirements: list[str]
    scope: str = "Observed obligations only; not full requirement or system compliance."


def build_report(execution: StoredExecution) -> CheckReport:
    result = execution.result
    checks = [RequirementCheck.model_validate(asdict(checker(result))) for checker in (
        check_disagreement_response, check_freshness_response,
        check_battery_response, check_transition_edges,
    )]
    available = {record.event_id for record in result.records}
    if any(not set(check.evidence_ids) <= available for check in checks):
        raise ValueError("checker emitted an unresolved evidence citation")
    return CheckReport(execution_id=execution.execution_id, run_id=result.run_id,
                       checks=checks, unassessed_requirements=["AT-REQ-004", "AT-REQ-005"])
