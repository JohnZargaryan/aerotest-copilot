import { useEffect, useRef, useState } from "react";
import type { EvidenceEvent } from "./EventTimeline";
import { parseInvestigation, requirementIds, type Investigation } from "./investigation-response";

export function InvestigationPanel({ executionId, runId, records }: {
  executionId: string; runId: string; records: EvidenceEvent[];
}) {
  const [selected, setSelected] = useState("all");
  const [answer, setAnswer] = useState<Investigation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => { pending.current?.abort(); }, []);
  async function load() {
    if (pending.current) return;
    const controller = new AbortController();
    pending.current = controller; setBusy(true); setError("");
    const timer = window.setTimeout(() => controller.abort(), 15000);
    try {
      const query = selected === "all" ? "" : `?requirement_id=${encodeURIComponent(selected)}`;
      const response = await fetch(`/api/v1/runs/${encodeURIComponent(executionId)}/investigation${query}`,
        { signal: controller.signal });
      if (!response.ok) {
        setError(response.status === 404 ? "This saved execution could not be found."
          : "Investigation could not be loaded. Check the local API and try again.");
        return;
      }
      setAnswer(parseInvestigation(await response.json(), executionId, runId, records, selected));
    } catch {
      setError(controller.signal.aborted ? "The investigation request was interrupted or timed out. Try again."
        : "No valid investigation was received. Check the local API and try again.");
    } finally {
      window.clearTimeout(timer); pending.current = null; setBusy(false);
    }
  }
  return <section className="investigation" aria-labelledby="investigation-title">
    <h3 id="investigation-title">Scripted investigation</h3>
    <p>Deterministic explanations from saved checks. No live AI model or free-form chat. This reads evidence without running another simulation.</p>
    <div className="investigation-controls">
      <label>Investigation focus<select value={selected} disabled={busy} onChange={event => {
        setSelected(event.target.value); setAnswer(null); setError("");
      }}><option value="all">All assessed requirements</option>
        {requirementIds.map(id => <option key={id} value={id}>{id}</option>)}
      </select></label>
      <button type="button" disabled={busy} onClick={load}>{busy ? "Investigating..." : "Explain saved checks"}</button>
    </div>
    <p role="status">{busy ? "Loading scripted investigation." : answer ? "Scripted explanation loaded." : "Select a focus and load its explanation."}</p>
    {error && <p role="alert" className="run-error">{error}</p>}
    {answer && <div className="investigation-answer">
      <p><strong>Scripted assistant {answer.assistant_version} · checker {answer.checker_version}</strong></p>
      <p>{answer.summary}</p><p>Scope: {answer.scope}</p>
      <p>Unassessed: {answer.unassessed_requirements.join(", ")}.</p>
      <div className="check-list">{answer.findings.map(finding => <article key={finding.requirement_id}>
        <h4>{finding.requirement_id} <span className={`verdict ${finding.status.toLowerCase()}`}>{finding.status}</span></h4>
        <p>{finding.explanation}</p><p className="check-scope">Scope: {finding.scope}</p>
        <details><summary>Resolved citations ({finding.citations.length} of {finding.total_evidence_count})</summary>
          {finding.citations.length === 0 && <p>No citations for this finding.</p>}
          <ul>{finding.citations.map(record => <li key={record.event_id}>
            <code>{record.event_id}</code><br />{record.sim_time_ms} ms delivery · {record.component_id} · {record.state}
            <pre>{JSON.stringify(record, null, 2)}</pre>
          </li>)}</ul>
        </details>
        {finding.omitted_evidence_count > 0 && <p>{finding.omitted_evidence_count} references omitted. This selection includes the first 10 and last 10 references; consult the full check report for the complete chain.</p>}
      </article>)}</div>
      <details className="tool-activity"><summary>Tool activity ({answer.tool_activity.length})</summary>
        <p>Recorded local operations for this response, in order.</p>
        <ol>{answer.tool_activity.map((entry, i) => <li key={i}>{i + 1}. <code>{entry}</code></li>)}</ol>
      </details>
    </div>}
  </section>;
}
