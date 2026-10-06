import { useRef, useState, type FormEvent } from "react";

import { EventTimeline, type EvidenceEvent } from "./EventTimeline";

const scenarios = [
  ["healthy-baseline", "Healthy baseline"],
  ["sensor-disagreement", "Sensor disagreement"],
  ["missing-messages", "Missing messages"],
  ["battery-degradation", "Battery degradation"],
] as const;

type SavedRun = {
  execution_id: string;
  created_at: string;
  result: {
    run_id: string;
    status: "completed";
    config: { scenario_id: string; seed: number; duration_ms: number };
    records: EvidenceEvent[];
  };
};

const failures: Record<string, string> = {
  RUN_CAPACITY: "The simulator is busy. Try again when the current runs finish.",
  START_FAILED: "The simulator is unavailable. Check that the local simulator is built.",
  TIMEOUT: "The simulation exceeded its time limit. No completed result was returned.",
  STORAGE_UNAVAILABLE: "The result could not be saved. Check the local API and storage.",
};

export function RunPanel() {
  const [scenario, setScenario] = useState<string>(scenarios[0][0]);
  const [seed, setSeed] = useState("42");
  const [duration, setDuration] = useState("30000");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState<SavedRun | null>(null);
  const pending = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const seedValue = Number(seed), durationValue = Number(duration);
    if (!seed.trim() || !duration.trim() || !Number.isInteger(seedValue)
        || seedValue < 0 || seedValue > 4294967295 || !Number.isInteger(durationValue)
        || durationValue < 1000 || durationValue > 120000 || durationValue % 100 !== 0) {
      setError("Use an integer seed from 0 to 4294967295 and a duration from 1000 to 120000 ms in steps of 100.");
      return;
    }
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/v1/runs", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: scenario, seed: seedValue,
          duration_ms: durationValue }), signal: AbortSignal.timeout(15000),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(response.status === 422 ? "The API rejected the configuration. Check your inputs."
          : failures[body?.detail?.code] ?? "The run could not complete. Check the local API and try again.");
        return;
      }
      const body = await response.json();
      if (typeof body.execution_id !== "string" || body.result?.status !== "completed"
          || !Array.isArray(body.result.records) || !body.result.config) {
        setError("The API returned an unexpected result. No summary can be displayed.");
        return;
      }
      setSaved(body as SavedRun);
    } catch {
      setError("No response was received. Check that the local API is running. A run may have been saved; retrying creates a new execution.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  const lastActive = saved?.result.records.slice().reverse().find(record => record.state !== "SHUTDOWN");
  const selectedLabel = scenarios.find(([id]) => id === saved?.result.config.scenario_id)?.[1];
  return <section className="run-panel" aria-labelledby="run-title">
    <div><p className="eyebrow">SIMULATION WORKBENCH</p>
      <h2 id="run-title">Run a scenario.</h2>
      <p>Repeatable sensor and power evidence, saved locally for investigation.</p></div>
    <form onSubmit={submit}>
      <fieldset disabled={busy}>
        <legend className="visually-hidden">Simulation configuration</legend>
        <label>Scenario<select value={scenario} onChange={event => setScenario(event.target.value)}>
          {scenarios.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
        </select></label>
        <label>Seed<input type="number" required min="0" max="4294967295" step="1"
          value={seed} onChange={event => setSeed(event.target.value)} /></label>
        <label>Duration (ms)<input type="number" required min="1000" max="120000" step="100"
          value={duration} onChange={event => setDuration(event.target.value)} /></label>
        <button type="submit">{busy ? "Running and saving..." : "Run simulation"}</button>
      </fieldset>
      <p className="input-hint">Fixed 100 ms ticks. The seed repeats the same evidence; each execution gets its own saved ID.</p>
    </form>
    <p role="status" aria-live="polite">{busy ? "Simulation in progress. Waiting for a saved result." : saved ? "Saved result available." : "Ready to run."}</p>
    {error && <p role="alert" className="run-error">{error}</p>}
    {saved && <div className="run-result">
      <h3>Last saved run</h3>
      <dl>
        <div><dt>Scenario</dt><dd>{selectedLabel ?? saved.result.config.scenario_id}</dd></div>
        <div><dt>Seed / duration</dt><dd>{saved.result.config.seed} / {saved.result.config.duration_ms} ms</dd></div>
        <div><dt>Evidence records</dt><dd>{saved.result.records.length}</dd></div>
        <div><dt>State before shutdown</dt><dd>{lastActive?.state ?? "Unavailable"}</dd></div>
        <div><dt>Execution ID</dt><dd className="identity">{saved.execution_id}</dd></div>
        <div><dt>Evidence run ID</dt><dd className="identity">{saved.result.run_id}</dd></div>
      </dl>
      <p>Simulation completed and saved. This is not a requirement verdict. Charts and investigation views are planned.</p>
      <EventTimeline key={saved.execution_id} records={saved.result.records} />
    </div>}
  </section>;
}
