"""Evaluation-only regression runner; application modules never load the answer keys."""

import argparse
import asyncio
import hashlib
import json
import platform
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from aerotest.assistant import InvestigationRequest, ScriptedInvestigator  # noqa: E402
from aerotest.contracts import SimulationConfig  # noqa: E402
from aerotest.reports import build_report  # noqa: E402
from aerotest.runner import run_simulation  # noqa: E402
from aerotest.storage import RunStore  # noqa: E402


def mutate(result, mutation):
    """Create an explicitly synthetic trace, preserving structural record identities."""
    result = result.model_copy(deep=True)
    if mutation is None:
        return result
    selected = [record for record in result.records
                if record.sim_time_ms == mutation["sim_time_ms"]
                and (mutation["component_id"] is None
                     or record.component_id == mutation["component_id"])]
    if not selected:
        raise ValueError("mutation matched no evidence")
    if mutation["operation"] == "replace_state":
        for record in selected:
            record.state = mutation["state"]
    elif mutation["operation"] == "drop_record":
        removed = {record.event_id for record in selected}
        result.records = [record for record in result.records if record.event_id not in removed]
        for sequence, record in enumerate(result.records):
            record.sequence = sequence
            record.event_id = f"{result.run_id}-e{sequence}"
    else:
        raise ValueError("unsupported evaluation mutation")
    return result


def grade(answer, execution, report, case):
    """Expected verdicts are independent keys; report fidelity is a separate metric."""
    expected = case["expected"]
    actual = {finding.requirement_id: finding.status for finding in answer.findings}
    checks = {check.requirement_id: check for check in report.checks}
    available = {record.event_id: record for record in execution.result.records}
    citations = [record for finding in answer.findings for record in finding.citations]
    grounded = sum(record.event_id in available and record == available[record.event_id]
                   for record in citations)
    fidelity = all(finding.requirement_id in checks
                   and (finding.status, finding.explanation, finding.scope) == (
                       checks[finding.requirement_id].status,
                       checks[finding.requirement_id].reason, checks[finding.requirement_id].scope)
                   for finding in answer.findings)
    evidence_selection = True
    activity = ["build_report"]
    for finding in answer.findings:
        check = checks.get(finding.requirement_id)
        if check is None:
            evidence_selection = False
            continue
        ids = list(dict.fromkeys(check.evidence_ids))
        selected = ids if len(ids) <= 20 else ids[:10] + ids[-10:]
        evidence_selection &= ([record.event_id for record in finding.citations] == selected
                               and finding.total_evidence_count == len(ids)
                               and finding.omitted_evidence_count == len(ids) - len(selected))
        if selected:
            activity.append("resolve_citations:" + finding.requirement_id)
    counts = {status: sum(f.status == status for f in answer.findings)
              for status in ("PASS", "FAIL", "INCONCLUSIVE")}
    summary_counts = all(f"{value} {status}" in answer.summary for status, value in counts.items())
    # Use the numeric summary prefix to avoid accepting '0 PASS' within '10 PASS'.
    prefix = (f"Scripted check summary: {counts['PASS']} PASS, {counts['FAIL']} FAIL, "
              f"{counts['INCONCLUSIVE']} INCONCLUSIVE in the selected checks. ")
    summary_counts &= answer.summary.startswith(prefix)
    witness = case.get("required_citation_time_ms")
    labels = (answer.mode == "scripted" and answer.unassessed_requirements == [
        "AT-REQ-004", "AT-REQ-005"] and "not a system compliance verdict" in answer.summary
        and answer.scope == report.scope)
    identity = (str(answer.execution_id) == execution.execution_id
                and answer.run_id == execution.result.run_id)
    obligations = {
        "verdicts": actual == expected and len(actual) == len(answer.findings),
        "grounded_citations": grounded == len(citations),
        "report_fidelity": fidelity,
        "evidence_selection": bool(evidence_selection),
        "summary_counts": bool(summary_counts),
        "scoped_labels": labels,
        "execution_identity": identity,
        "tool_activity": answer.tool_activity == activity,
        "required_witness": witness is None or any(r.sim_time_ms == witness for r in citations),
    }
    return {"case_id": case["case_id"], "synthetic": case["mutation"] is not None,
            "expected": expected, "actual": actual, "checks": obligations,
            "passed": all(obligations.values()), "citation_count": len(citations),
            "grounded_citation_count": grounded,
            "verdict_matches": sum(actual.get(key) == value for key, value in expected.items()),
            "expected_finding_count": len(expected)}


def dataset_digest(dataset):
    canonical = json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


async def evaluate():
    raw = (ROOT / "evaluation/scripted-cases.json").read_bytes()
    dataset = json.loads(raw)
    if dataset["dataset_version"] != "1.0" or not 1 <= len(dataset["cases"]) <= 100:
        raise ValueError("unsupported evaluation dataset")
    ids = [case["case_id"] for case in dataset["cases"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate evaluation case identity")
    results = []
    with tempfile.TemporaryDirectory(prefix="aerotest-evaluation-") as temporary:
        store = RunStore(Path(temporary) / "evaluation.sqlite")
        assistant = ScriptedInvestigator(store)
        for case in dataset["cases"]:
            config = SimulationConfig.model_validate(case["config"])
            result = mutate(await run_simulation(config), case["mutation"])
            saved = store.save(result)
            report = build_report(saved)
            request = InvestigationRequest(execution_id=saved.execution_id,
                                           requirement_id=case["requirement_id"])
            answer = assistant.investigate(request)
            graded = grade(answer, saved, report, case)
            graded["repeatable"] = answer == assistant.investigate(request)
            graded["storage_unchanged"] = saved == store.get(saved.execution_id)
            graded["passed"] &= graded["repeatable"] and graded["storage_unchanged"]
            results.append(graded)
    return {"dataset_version": dataset["dataset_version"],
            "dataset_sha256": dataset_digest(dataset),
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "environment": {"python": platform.python_version(), "platform": sys.platform},
            "versions": {"simulator": result.simulator_version,
                         "assistant": answer.assistant_version, "checker": answer.checker_version},
            "metrics": {"cases": len(results), "passed": sum(r["passed"] for r in results),
                        "expected_findings": sum(r["expected_finding_count"] for r in results),
                        "verdict_matches": sum(r["verdict_matches"] for r in results),
                        "citations": sum(r["citation_count"] for r in results),
                        "grounded_citations": sum(r["grounded_citation_count"] for r in results)},
            "results": results}


def comparable(report):
    return {key: value for key, value in report.items()
            if key not in ("generated_at_utc", "environment")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/scripted-evaluation.json")
    parser.add_argument("--check", action="store_true",
                        help="Compare deterministic results to the committed evaluation report")
    args = parser.parse_args()
    report = asyncio.run(evaluate())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"]))
    if report["metrics"]["passed"] != report["metrics"]["cases"]:
        raise SystemExit("Scripted evaluation failed; inspect the output report.")
    if args.check:
        snapshot_path = ROOT / "evaluation/scripted-report.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if comparable(report) != comparable(snapshot):
            raise SystemExit("Scripted evaluation results differ from the committed report.")


if __name__ == "__main__":
    main()
