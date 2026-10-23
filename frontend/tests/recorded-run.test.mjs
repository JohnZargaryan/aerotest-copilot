import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { parseRecordedRun, recordedScenarios } from "../src/recorded-run.ts";

const directory = new URL("../public/recorded/", import.meta.url);
const read = file => JSON.parse(readFileSync(new URL(file, directory), "utf8"));
const bundle = () => read("sensor-disagreement.json");

test("all four exported files match the manifest and retain grounded reports for every focus", () => {
  const manifest = read("manifest.json");
  assert.deepEqual(manifest.scenarios.map(entry => entry.scenario_id), recordedScenarios.map(([id]) => id));
  const identities = new Set();
  for (const entry of manifest.scenarios) {
    const raw = readFileSync(new URL(entry.file, directory));
    assert.equal(raw.length, entry.bytes);
    assert.equal(createHash("sha256").update(raw).digest("hex"), entry.sha256);
    const saved = parseRecordedRun(JSON.parse(raw), entry.scenario_id);
    assert.equal(saved.source_revision, manifest.source_revision);
    assert(!identities.has(saved.execution.execution_id));
    identities.add(saved.execution.execution_id);
    assert.equal(Object.keys(saved.investigations).length, 5);
    assert.deepEqual(saved.report.unassessed_requirements, ["AT-REQ-004", "AT-REQ-005"]);
    for (const record of saved.execution.result.records) assert.equal(record.run_id, saved.execution.result.run_id);
  }
});

test("recorded loader rejects a wrong scenario, execution, run, version and missing focus", () => {
  assert.throws(() => parseRecordedRun(bundle(), "healthy-baseline"));
  const mutations = [
    v => { v.mode = "live"; },
    v => { v.schema_version = "2.0"; },
    v => { v.report.execution_id = "other"; },
    v => { v.investigations.all.run_id = "other"; },
    v => { delete v.investigations["AT-REQ-006"]; },
    v => { v.execution.result.records[1].event_id = v.execution.result.records[0].event_id; },
    v => { v.execution.result.records[0].sequence = 99; },
    v => { v.execution.result.records[0].run_id = "other"; },
  ];
  for (const mutate of mutations) {
    const value = bundle(); mutate(value);
    assert.throws(() => parseRecordedRun(value, "sensor-disagreement"));
  }
});

test("recorded citations and verdicts cannot silently diverge from original evidence and checks", () => {
  const mutations = [
    v => { v.investigations.all.findings[0].citations[0].state = "SAFE"; },
    v => { v.investigations.all.findings[0].status = "FAIL"; },
    v => { v.report.checks[0].evidence_ids = ["nonexistent"]; },
    v => { v.investigations["AT-REQ-001"].findings[0].explanation = "Different reason"; },
  ];
  for (const mutate of mutations) {
    const value = bundle(); mutate(value);
    assert.throws(() => parseRecordedRun(value, "sensor-disagreement"));
  }
});
