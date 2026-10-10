import test from "node:test";
import assert from "node:assert/strict";
import { parseInvestigation } from "../src/investigation-response.ts";
const records = Array.from({length: 30}, (_, i) => ({event_id: "e" + i, run_id: "run", sequence: i,
  sim_time_ms: i * 100, component_id: "battery", event_code: "POWER_SAMPLE", state: "SAFE",
  severity: "INFO", measurement: 900, unit: "basis_points", details: {source: "recorded"}}));
const response = () => ({mode: "scripted", assistant_version: "0.1.0", checker_version: "0.1.0",
  execution_id: "exec", run_id: "run", summary: "Scoped observations", scope: "Observed only",
  unassessed_requirements: ["AT-REQ-004", "AT-REQ-005"], tool_activity: ["build_report", "resolve_citations:AT-REQ-003"],
  findings: [{requirement_id: "AT-REQ-003", status: "PASS", explanation: "Recorded response", scope: "Battery",
    citations: [records[0], records[1]], total_evidence_count: 2, omitted_evidence_count: 0}]});
const parse = (data, selected = "AT-REQ-003") => parseInvestigation(data, "exec", "run", records, selected);
test("selected findings preserve all verdicts and original citations", () => {
  for (const status of ["PASS", "FAIL", "INCONCLUSIVE"]) {
    const input = response(); input.findings[0].status = status;
    assert.deepEqual(parse(input), input);
  }
});
test("foreign identities, modes and selection mismatches cannot display", () => {
  for (const key of ["execution_id", "run_id", "mode"]) {
    const input = response(); input[key] = "other"; assert.throws(() => parse(input));
  }
  assert.throws(() => parse(response(), "AT-REQ-001"));
  assert.throws(() => parse(response(), "all"));
  assert.throws(() => parse(response(), "AT-REQ-005"));
});
test("modified, missing or duplicate evidence aborts the complete response", () => {
  for (const mutation of [r => r.findings[0].citations[0].measurement++,
    r => r.findings[0].citations[0].details.source = "altered",
    r => r.findings[0].citations[0].event_id = "foreign",
    r => r.findings[0].citations[1] = r.findings[0].citations[0]]) {
    const input = structuredClone(response()); mutation(input); assert.throws(() => parse(input));
  }
  const reordered = response(); reordered.findings[0].citations = records.slice(0, 2).map(r => Object.fromEntries(Object.entries(r).reverse()));
  assert.deepEqual(parse(reordered), reordered);
});
test("long citation selections must disclose consistent omission counts", () => {
  const input = response(); const f = input.findings[0];
  f.citations = [...records.slice(0, 10), ...records.slice(-10)];
  f.total_evidence_count = 30; f.omitted_evidence_count = 10;
  assert.equal(parse(input).findings[0].omitted_evidence_count, 10);
  f.omitted_evidence_count = 0; assert.throws(() => parse(input));
  f.omitted_evidence_count = 10; f.citations.push(records[11]); assert.throws(() => parse(input));
});
test("all requirements need unique findings and activity matching actual lookups", () => {
  const input = response(); input.findings = ["001", "002", "003", "006"].map(n => ({...input.findings[0], requirement_id: "AT-REQ-" + n}));
  input.tool_activity = ["build_report", ...input.findings.map(f => "resolve_citations:" + f.requirement_id)];
  assert.equal(parse(input, "all").findings.length, 4);
  input.findings[1].requirement_id = "AT-REQ-001"; assert.throws(() => parse(input, "all"));
  const bad = response(); bad.tool_activity.push("live_model"); assert.throws(() => parse(bad));
  bad.tool_activity = ["build_report"]; assert.throws(() => parse(bad));
  for (const value of [null, {}, {...response(), unassessed_requirements: []}, {...response(), unassessed_requirements: [["AT-REQ-004"], ["AT-REQ-005"]]}]) assert.throws(() => parse(value));
});
