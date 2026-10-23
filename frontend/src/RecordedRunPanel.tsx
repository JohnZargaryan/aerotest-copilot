import { useEffect, useState } from "react";
import { EventTimeline } from "./EventTimeline";
import { TelemetryCharts } from "./TelemetryCharts";
import { RequirementResults } from "./RequirementResults";
import { InvestigationPanel } from "./InvestigationPanel";
import { parseRecordedRun, recordedScenarios, type RecordedRun } from "./recorded-run";

export function RecordedRunPanel() {
  const [scenario, setScenario] = useState("sensor-disagreement");
  const [saved, setSaved] = useState<RecordedRun | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setSaved(null); setError("");
    const timer = window.setTimeout(() => controller.abort(), 15000);
    async function load() {
      try {
        const response = await fetch(`./recorded/${scenario}.json`, { signal: controller.signal });
        if (!response.ok) throw new Error("Unavailable snapshot");
        const bundle = parseRecordedRun(await response.json(), scenario);
        if (!controller.signal.aborted) setSaved(bundle);
      } catch {
        if (active) setError("The recorded run could not be loaded or verified, or the request timed out. Try again.");
      } finally { window.clearTimeout(timer); }
    }
    void load();
    return () => { active = false; window.clearTimeout(timer); controller.abort(); };
  }, [scenario, retry]);
  const result = saved?.execution.result;
  const lastActive = result?.records.slice().reverse().find(record => record.state !== "SHUTDOWN");
  return <section className="run-panel" aria-labelledby="run-title">
    <p className="eyebrow">RECORDED RUN EXPLORER</p>
    <h2 id="run-title">Choose a scenario. Trace the response.</h2>
    <p>These are real outputs from the C++ simulator, captured at seed 42 with 100 ms ticks. Selecting a scenario loads its saved evidence; it does not run a new simulation.</p>
    <label className="recorded-selector">Recorded scenario<select value={scenario} onChange={event => setScenario(event.target.value)}>
      {recordedScenarios.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
    </select></label>
    <p>{recordedScenarios.find(([id]) => id === scenario)?.[2]}</p>
    <p role="status" aria-live="polite">{error ? "Recorded run unavailable." : saved ? "Recorded evidence loaded. Explore the charts, checks and timeline below." : "Loading recorded evidence…"}</p>
    {error && <div role="alert"><p className="run-error">{error}</p><button onClick={() => setRetry(value => value + 1)}>Retry loading recorded run</button></div>}
    {saved && result && <div className="run-result" key={saved.execution.execution_id}>
      <h3>Recorded execution</h3>
      <dl>
        <div><dt>Duration / seed</dt><dd>{result.config.duration_ms / 1000} seconds / {result.config.seed}</dd></div>
        <div><dt>Evidence records</dt><dd>{result.records.length}</dd></div>
        <div><dt>State before shutdown</dt><dd>{lastActive?.state ?? "Unavailable"}</dd></div>
        <div><dt>Captured (UTC)</dt><dd>{saved.execution.created_at.replace("T", " ").replace(/\.\d+Z$/, "Z")}</dd></div>
      </dl>
      <nav className="recorded-nav" aria-label="Evidence sections"><a href="#telemetry-title">Telemetry ↓</a><a href="#checks-title">Requirement checks ↓</a><a href="#timeline-title">Event timeline ↓</a></nav>
      <TelemetryCharts records={result.records} durationMs={result.config.duration_ms} />
      <RequirementResults executionId={saved.execution.execution_id} runId={result.run_id} records={result.records} loadReport={async () => saved.report} />
      <InvestigationPanel executionId={saved.execution.execution_id} runId={result.run_id} records={result.records} loadInvestigation={async focus => saved.investigations[focus]} />
      <EventTimeline records={result.records} />
      <details className="recorded-provenance"><summary>Recording provenance & download</summary>
        <p>Execution: <code>{saved.execution.execution_id}</code><br />Evidence run: <code>{result.run_id}</code><br />Simulator: {result.simulator_version}<br />Simulator/checker source: <a href={`https://github.com/JohnZargaryan/aerotest-copilot/tree/${saved.source_revision}`} target="_blank" rel="noreferrer">{saved.source_revision.slice(0, 12)}</a></p>
        <p><a href={`./recorded/${scenario}.json`} download>Download complete recorded evidence & reports (JSON)</a> · <a href="./recorded/manifest.json" target="_blank" rel="noreferrer">File sizes & SHA-256 hashes</a></p>
        <p>Reports assess observed obligations only. Configuration validation and deterministic replay are not assessed by these runtime checkers. Explanations are scripted from the saved report.</p>
      </details>
    </div>}
  </section>;
}
