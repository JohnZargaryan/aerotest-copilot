"""Export real simulator executions and scripted reports for the browser-only demo."""

import asyncio
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from aerotest.assistant import InvestigationRequest, ScriptedInvestigator  # noqa: E402
from aerotest.contracts import SimulationConfig  # noqa: E402
from aerotest.reports import build_report  # noqa: E402
from aerotest.runner import run_simulation  # noqa: E402
from aerotest.storage import RunStore  # noqa: E402

SCENARIOS = ["healthy-baseline", "sensor-disagreement", "missing-messages",
             "battery-degradation"]
FOCUSES = ["all", "AT-REQ-001", "AT-REQ-002", "AT-REQ-003", "AT-REQ-006"]


async def export():
    output = ROOT / "frontend" / "public" / "recorded"
    output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
        cwd=ROOT, text=True).strip()
    entries = []
    with tempfile.TemporaryDirectory(prefix="aerotest-demo-") as directory:
        store = RunStore(Path(directory) / "runs.sqlite")
        investigator = ScriptedInvestigator(store)
        for scenario in SCENARIOS:
            execution = store.save(await run_simulation(SimulationConfig(
                scenario_id=scenario, seed=42, duration_ms=30000)))
            investigations = {focus: investigator.investigate(InvestigationRequest(
                execution_id=execution.execution_id,
                requirement_id=None if focus == "all" else focus,
            )).model_dump(mode="json") for focus in FOCUSES}
            bundle = {"schema_version": "1.0", "mode": "recorded",
                      "source_revision": revision,
                      "execution": execution.model_dump(mode="json"),
                      "report": build_report(execution).model_dump(mode="json"),
                      "investigations": investigations}
            raw = (json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
            (output / f"{scenario}.json").write_bytes(raw)
            entries.append({"scenario_id": scenario, "file": f"{scenario}.json",
                            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    (output / "manifest.json").write_text(json.dumps({"schema_version": "1.0",
        "mode": "recorded", "source_revision": revision, "scenarios": entries}, indent=2) + "\n",
        encoding="utf-8")
    print(f"Exported {len(entries)} actual executions ({sum(e['bytes'] for e in entries)} bytes).")


if __name__ == "__main__":
    asyncio.run(export())
