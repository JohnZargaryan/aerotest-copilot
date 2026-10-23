import type { EvidenceEvent } from "./EventTimeline";
import { parseCheckReport, type CheckReport } from "./check-report.ts";
import { parseInvestigation, requirementIds, type Investigation } from "./investigation-response.ts";

export const recordedScenarios = [
  ["healthy-baseline", "Healthy baseline", "Start with a nominal reference run."],
  ["sensor-disagreement", "Sensor disagreement", "Trace the sensor mismatch into a degraded state."],
  ["missing-messages", "Missing messages", "Inspect delayed deliveries and the freshness response."],
  ["battery-degradation", "Battery degradation", "Follow falling battery charge and safe-state entry."],
] as const;
export type RecordedRun = {
  schema_version: "1.0"; mode: "recorded"; source_revision: string;
  execution: { execution_id: string; created_at: string; result: {
    run_id: string; status: "completed"; simulator_version: string;
    config: { scenario_id: string; seed: number; duration_ms: number; step_ms: number };
    records: EvidenceEvent[];
  } };
  report: CheckReport; investigations: Record<string, Investigation>;
};

// Validate identities and every resolved citation before showing a saved bundle.
export function parseRecordedRun(input: unknown, scenario: string): RecordedRun {
  const value = input as RecordedRun | null;
  const execution = value?.execution, result = execution?.result;
  if (value?.schema_version !== "1.0" || value.mode !== "recorded"
      || !/^[a-f0-9]{40}$/.test(value.source_revision)
      || typeof execution?.execution_id !== "string" || !execution.execution_id
      || !Number.isFinite(Date.parse(execution.created_at))
      || typeof result?.run_id !== "string" || !result.run_id || result.status !== "completed"
      || result.config?.scenario_id !== scenario || result.config.seed !== 42
      || result.config.duration_ms !== 30000 || result.config.step_ms !== 100
      || !Array.isArray(result.records) || !result.records.length || result.records.length > 4000) {
    throw new Error("Invalid recorded execution");
  }
  const ids = new Set<string>();
  for (const [index, record] of result.records.entries()) {
    if (typeof record.event_id !== "string" || !record.event_id || ids.has(record.event_id)
        || (record as EvidenceEvent & { run_id?: unknown }).run_id !== result.run_id
        || record.sequence !== index || !Number.isInteger(record.sim_time_ms)
        || record.sim_time_ms < 0 || record.sim_time_ms > result.config.duration_ms
        || typeof record.component_id !== "string" || typeof record.state !== "string"
        || typeof record.event_code !== "string" || typeof record.severity !== "string"
        || (record.measurement !== null && !Number.isFinite(record.measurement))
        || typeof record.unit !== "string" || !record.details || typeof record.details !== "object") {
      throw new Error("Invalid recorded evidence");
    }
    ids.add(record.event_id);
  }
  value.report = parseCheckReport(value.report, execution.execution_id, result.run_id, [...ids]);
  for (const focus of ["all", ...requirementIds]) {
    const answer = parseInvestigation(value.investigations?.[focus], execution.execution_id,
      result.run_id, result.records, focus);
    for (const finding of answer.findings) {
      const check = value.report.checks.find(c => c.requirement_id === finding.requirement_id)!;
      if (finding.status !== check.status || finding.explanation !== check.reason
          || finding.scope !== check.scope
          || finding.total_evidence_count !== new Set(check.evidence_ids).size
          || finding.citations.some(record => !check.evidence_ids.includes(record.event_id))) {
        throw new Error("Recorded explanation does not match its check");
      }
    }
    value.investigations[focus] = answer;
  }
  return value;
}
