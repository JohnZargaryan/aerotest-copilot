import { useEffect, useRef, useState } from "react";
import type { EvidenceEvent } from "./EventTimeline";
import { parseCheckReport, type CheckReport } from "./check-report";

export function RequirementResults({ executionId, runId, records }: {
  executionId: string; runId: string; records: EvidenceEvent[];
}) {
  const [report, setReport] = useState<CheckReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => { pending.current?.abort(); }, []);

  async function load() {
    if (pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    setError("");
    const timer = window.setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(`/api/v1/runs/${encodeURIComponent(executionId)}/checks`,
        { signal: controller.signal });
      if (!response.ok) {
        setError(response.status === 404 ? "This saved execution could not be found."
          : "Checks could not be loaded. Check the local API and try again.");
        return;
      }
      setReport(parseCheckReport(await response.json(), executionId, runId,
        records.map(record => record.event_id)));
    } catch {
      if (!controller.signal.aborted) setError("No valid check report was received. Check the local API and try again.");
      else setError("The check request was interrupted or timed out. Try loading the checks again.");
    } finally {
      window.clearTimeout(timer);
      pending.current = null;
      setBusy(false);
    }
  }

  const evidence = new Map(records.map(record => [record.event_id, record]));
  return <section className="requirement-results" aria-labelledby="checks-title">
    <h3 id="checks-title">Requirement checks</h3>
    <p>Assess observed obligations in this saved execution. Inconclusive checks are not passes, and unassessed requirements remain explicit.</p>
    <button type="button" disabled={busy} onClick={load}>{busy ? "Loading checks..." : report ? "Reload requirement checks" : "Load requirement checks"}</button>
    <p role="status">{busy ? "Loading saved-evidence checks." : report ? "Check report loaded." : "Checks have not been loaded."}</p>
    {error && <p role="alert" className="run-error">{error}</p>}
    {report && <div>
      <p><strong>Checker version {report.checker_version}</strong><br />{report.scope}</p>
      <p>Unassessed: {report.unassessed_requirements.join(", ") || "None listed"}.</p>
      <div className="check-list">{report.checks.map(check => <article key={check.requirement_id}>
        <h4>{check.requirement_id} <span className={`verdict ${check.status.toLowerCase()}`}>{check.status}</span></h4>
        <p>{check.reason}</p><p className="check-scope">Scope: {check.scope}</p>
        <details><summary>Evidence references ({check.evidence_ids.length})</summary>
          {check.evidence_ids.length === 0 ? <p>No evidence references were returned for this check.</p>
            : <ul>{check.evidence_ids.slice(0, 20).map(id => {
              const record = evidence.get(id)!;
              return <li key={id}><code>{id}</code><br />{record.sim_time_ms} ms delivery · {record.component_id} · {record.state}</li>;
            })}</ul>}
          {check.evidence_ids.length > 20 && <p>Showing the first 20 of {check.evidence_ids.length} references. The full report is available through the check API.</p>}
        </details>
      </article>)}</div>
    </div>}
  </section>;
}
