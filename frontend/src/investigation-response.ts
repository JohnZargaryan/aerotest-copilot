import type { EvidenceEvent } from "./EventTimeline";

export const requirementIds = ["AT-REQ-001", "AT-REQ-002", "AT-REQ-003", "AT-REQ-006"] as const;
export type Investigation = {
  mode: "scripted"; assistant_version: string; checker_version: string;
  execution_id: string; run_id: string; summary: string; scope: string;
  unassessed_requirements: string[]; tool_activity: string[];
  findings: { requirement_id: string; status: "PASS" | "FAIL" | "INCONCLUSIVE";
    explanation: string; scope: string; citations: EvidenceEvent[];
    total_evidence_count: number; omitted_evidence_count: number }[];
};
const object = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0 && v.length <= 10000;
const count = (v: unknown): v is number => typeof v === "number" && Number.isInteger(v) && v >= 0 && v <= 4000;
function same(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (!object(a) || !object(b)) return false;
  const keys = Object.keys(a);
  return keys.length === Object.keys(b).length && keys.every(key => Object.hasOwn(b, key) && same(a[key], b[key]));
}

export function parseInvestigation(data: unknown, executionId: string, runId: string,
                                   records: EvidenceEvent[], selected: string): Investigation {
  const invalid = () => { throw new Error("INVALID_INVESTIGATION"); };
  const expected = selected === "all" ? [...requirementIds] : requirementIds.filter(id => id === selected);
  if (!object(data) || data.mode !== "scripted" || data.assistant_version !== "0.1.0"
      || !text(data.checker_version) || data.execution_id !== executionId || data.run_id !== runId
      || !text(data.summary) || !text(data.scope) || expected.length === 0
      || !Array.isArray(data.findings) || data.findings.length !== expected.length
      || !Array.isArray(data.unassessed_requirements)
      || data.unassessed_requirements.length !== 2
      || data.unassessed_requirements[0] !== "AT-REQ-004" || data.unassessed_requirements[1] !== "AT-REQ-005"
      || !Array.isArray(data.tool_activity)) return invalid();
  const available = new Map(records.map(record => [record.event_id, record]));
  const activity = ["build_report"];
  const remaining = new Set<string>(expected);
  for (const finding of data.findings) {
    if (!object(finding) || !text(finding.requirement_id) || !remaining.delete(finding.requirement_id)
        || typeof finding.status !== "string" || !["PASS", "FAIL", "INCONCLUSIVE"].includes(finding.status)
        || !text(finding.explanation) || !text(finding.scope) || !Array.isArray(finding.citations)
        || finding.citations.length > 20 || !count(finding.total_evidence_count)
        || !count(finding.omitted_evidence_count)
        || finding.total_evidence_count !== finding.citations.length + finding.omitted_evidence_count
        || finding.citations.length !== Math.min(20, finding.total_evidence_count)) return invalid();
    const seen = new Set<string>();
    for (const citation of finding.citations) {
      if (!object(citation) || !text(citation.event_id) || seen.has(citation.event_id)
          || !same(citation, available.get(citation.event_id))) return invalid();
      seen.add(citation.event_id);
    }
    if (finding.citations.length) activity.push("resolve_citations:" + finding.requirement_id);
  }
  if (data.tool_activity.length !== activity.length
      || !data.tool_activity.every((entry, i) => entry === activity[i])) return invalid();
  return data as Investigation;
}
