"""Scoring failures must be detected even when runtime output is internally consistent."""

import json
from copy import deepcopy
from types import SimpleNamespace as Obj

from scripts.evaluate_scripted import comparable, dataset_digest, grade, mutate


def sample():
    record = Obj(event_id="event", sim_time_ms=9100, measurement=900,
                 state="SAFE", details={"sample_time_ms": 9100})
    execution = Obj(execution_id="exec", result=Obj(run_id="run", records=[record]))
    check = Obj(requirement_id="AT-REQ-003", status="PASS", reason="Observed response",
                scope="Power only", evidence_ids=["event"])
    report = Obj(checks=[check], scope="Observed only")
    finding = Obj(requirement_id="AT-REQ-003", status="PASS", explanation=check.reason,
                  scope=check.scope, citations=[deepcopy(record)], total_evidence_count=1,
                  omitted_evidence_count=0)
    answer = Obj(findings=[finding], execution_id="exec", run_id="run", mode="scripted",
                 summary="Scripted check summary: 1 PASS, 0 FAIL, 0 INCONCLUSIVE in the selected "
                         "checks. These are scoped observations, not a system compliance verdict.",
                 scope=report.scope, unassessed_requirements=["AT-REQ-004", "AT-REQ-005"],
                 tool_activity=["build_report", "resolve_citations:AT-REQ-003"])
    case = {"case_id": "example", "mutation": None, "expected": {"AT-REQ-003": "PASS"},
            "required_citation_time_ms": 9100}
    return answer, execution, report, case


def test_grade_accepts_grounded_scoped_response():
    result = grade(*sample())
    assert result["passed"] and result["verdict_matches"] == 1
    assert result["grounded_citation_count"] == result["citation_count"] == 1


def test_oracle_rejects_wrong_verdict_even_when_checker_and_assistant_agree():
    answer, execution, report, case = sample()
    answer.findings[0].status = report.checks[0].status = "FAIL"
    result = grade(answer, execution, report, case)
    assert result["checks"]["report_fidelity"]
    assert not result["passed"] and not result["checks"]["verdicts"]


def test_grader_rejects_changed_or_foreign_citation_content():
    for field, value in [("measurement", 10000), ("details", {"sample_time_ms": 9200}),
                         ("event_id", "unresolved")]:
        answer, execution, report, case = sample()
        setattr(answer.findings[0].citations[0], field, value)
        result = grade(answer, execution, report, case)
        assert not result["passed"] and result["grounded_citation_count"] == 0


def test_grader_rejects_bad_counts_scope_identity_and_tool_activity():
    for field, value in [("summary", "Scripted check summary: 10 PASS, 0 FAIL, 0 INCONCLUSIVE "
                         "in the selected checks. not a system compliance verdict"),
                         ("execution_id", "other"), ("mode", "live"),
                         ("unassessed_requirements", []), ("tool_activity", ["build_report"])]:
        answer, execution, report, case = sample()
        setattr(answer, field, value)
        assert not grade(answer, execution, report, case)["passed"]
    answer, execution, report, case = sample()
    answer.findings[0].omitted_evidence_count = 1
    assert not grade(answer, execution, report, case)["checks"]["evidence_selection"]
    case["required_citation_time_ms"] = 9200
    assert not grade(answer, execution, report, case)["checks"]["required_witness"]


def test_comparison_ignores_only_run_timestamp_and_host_metadata():
    original = {"generated_at_utc": "one", "environment": {"platform": "win32"},
                "dataset_sha256": "digest", "metrics": {"passed": 12}}
    later = deepcopy(original)
    later.update(generated_at_utc="two", environment={"platform": "linux"})
    assert comparable(original) == comparable(later)
    later["metrics"]["passed"] = 11
    assert comparable(original) != comparable(later)


def test_synthetic_mutation_never_changes_original_records():
    class Trace(Obj):
        def model_copy(self, deep):
            assert deep
            return deepcopy(self)
    record = Obj(event_id="run-e0", component_id="battery", sim_time_ms=9100, state="SAFE")
    original = Trace(run_id="run", records=[record])
    defective = mutate(original, {"operation": "replace_state", "sim_time_ms": 9100,
                                  "component_id": "battery", "state": "DEGRADED"})
    assert original.records[0].state == "SAFE"
    assert defective.records[0].state == "DEGRADED"



def test_dataset_digest_is_portable_but_detects_changed_expected_answers():
    lf = '{\n"expected": {"AT-REQ-003": "FAIL"},\n"seed": 887\n}'
    crlf = lf.replace("\n", "\r\n")
    reordered = '{"seed":887,"expected":{"AT-REQ-003":"FAIL"}}'
    assert dataset_digest(json.loads(lf)) == dataset_digest(json.loads(crlf))
    assert dataset_digest(json.loads(lf)) == dataset_digest(json.loads(reordered))
    assert dataset_digest(json.loads(lf)) != dataset_digest(json.loads(lf.replace("FAIL", "PASS")))
