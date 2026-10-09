export type CheckReport = {
  schema_version: string; checker_version: string; execution_id: string; run_id: string;
  checks: { requirement_id: string; status: "PASS" | "FAIL" | "INCONCLUSIVE";
    reason: string; scope: string; evidence_ids: string[] }[];
  unassessed_requirements: string[]; scope: string;
};
const object = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === "string" && value.length > 0;

export function parseCheckReport(data: unknown, executionId: string, runId: string,
                                 eventIds: string[]): CheckReport {
  const available = new Set(eventIds);
  const requirements = new Set(["AT-REQ-001", "AT-REQ-002", "AT-REQ-003", "AT-REQ-006"]);
  if (!object(data) || data.schema_version !== "1.0" || !text(data.checker_version)
      || data.execution_id !== executionId || data.run_id !== runId || !text(data.scope)
      || !Array.isArray(data.checks) || data.checks.length !== 4
      || !Array.isArray(data.unassessed_requirements)
      || data.unassessed_requirements.length > 6 || !data.unassessed_requirements.every(text)) {
    throw new Error("INVALID_CHECK_REPORT");
  }
  for (const check of data.checks) {
    if (!object(check) || !text(check.requirement_id) || !requirements.delete(check.requirement_id)
        || typeof check.status !== "string" || !["PASS", "FAIL", "INCONCLUSIVE"].includes(check.status)
        || !text(check.reason) || !text(check.scope) || !Array.isArray(check.evidence_ids)
        || check.evidence_ids.length > 4000
        || !check.evidence_ids.every(id => typeof id === "string" && available.has(id))) {
      throw new Error("INVALID_CHECK_REPORT");
    }
  }
  return data as CheckReport;
}
