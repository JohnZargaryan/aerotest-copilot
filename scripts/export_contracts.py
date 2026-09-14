"""Export public schemas. --check detects stale committed schemas without writing."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from aerotest.contracts import EventRecord, SimulationConfig  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
for name, model in [("simulation-config", SimulationConfig), ("event-record", EventRecord)]:
    output = ROOT / "contracts" / f"{name}.schema.json"
    serialized = json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != serialized:
            raise SystemExit(f"Stale schema: {output.name}; run scripts/export_contracts.py")
    else:
        output.write_text(serialized, encoding="utf-8")
