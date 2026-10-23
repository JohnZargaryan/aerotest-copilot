"""Public recordings must reproduce current runtime reports, without evaluation keys."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aerotest.assistant import InvestigationRequest, ScriptedInvestigator
from aerotest.reports import build_report
from aerotest.runner import _decode
from aerotest.storage import StoredExecution

DIRECTORY = Path(__file__).resolve().parents[2] / "frontend" / "public" / "recorded"


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                     "missing-messages", "battery-degradation"])
def test_recorded_bundle_reproduces_runtime_reports(scenario):
    bundle = json.loads((DIRECTORY / f"{scenario}.json").read_text(encoding="utf-8"))
    execution = StoredExecution.model_validate(bundle["execution"])
    _decode(execution.result.model_dump_json().encode(), execution.result.config)
    assert execution.result.config.scenario_id == scenario
    assert build_report(execution).model_dump(mode="json") == bundle["report"]
    store = SimpleNamespace(get=lambda identity: execution
                            if identity == execution.execution_id else None)
    investigator = ScriptedInvestigator(store)
    for focus, expected in bundle["investigations"].items():
        actual = investigator.investigate(InvestigationRequest(
            execution_id=execution.execution_id,
            requirement_id=None if focus == "all" else focus))
        assert actual.model_dump(mode="json") == expected
