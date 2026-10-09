import test from "node:test";
import assert from "node:assert/strict";
import { parseCheckReport } from "../src/check-report.ts";
const report = () => ({ schema_version: "1.0", checker_version: "0.1.0", execution_id: "exec",
  run_id: "run", scope: "Observed only", unassessed_requirements: ["AT-REQ-004", "AT-REQ-005"],
  checks: ["001", "002", "003", "006"].map((n, i) => ({ requirement_id: "AT-REQ-" + n,
    status: ["PASS", "FAIL", "INCONCLUSIVE", "PASS"][i], reason: "Observed reason",
    scope: "Scoped check", evidence_ids: ["event"] })) });
test("all statuses, reasons and unassessed requirements are preserved", () => {
  const input = report();
  assert.deepEqual(parseCheckReport(input, "exec", "run", ["event"]), input);
});
test("another execution or evidence run cannot be presented as the current report", () => {
  for (const key of ["execution_id", "run_id"]) {
    const input = report(); input[key] = "other";
    assert.throws(() => parseCheckReport(input, "exec", "run", ["event"]));
  }
});
test("unresolved citations and duplicate or missing checks are rejected", () => {
  const cases = [report(), report(), report()];
  cases[0].checks[0].evidence_ids = ["missing"];
  cases[1].checks[1].requirement_id = "AT-REQ-001";
  cases[2].checks.pop();
  for (const input of cases) assert.throws(() => parseCheckReport(input, "exec", "run", ["event"]));
});
test("malformed status, reason, references and top-level responses are rejected", () => {
  const cases = [null, {}, report(), report(), report(), report(), report()];
  cases[2].checks[0].status = "APPROVED";
  cases[3].checks[0].reason = null;
  cases[4].checks[0].evidence_ids = Array(4001).fill("event");
  cases[5].unassessed_requirements = [null];
  cases[6].checks[0].status = ["PASS"];
  for (const input of cases) assert.throws(() => parseCheckReport(input, "exec", "run", ["event"]));
});
