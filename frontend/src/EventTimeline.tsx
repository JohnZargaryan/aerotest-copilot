import { useState } from "react";

export type EvidenceEvent = {
  event_id: string;
  sequence: number;
  sim_time_ms: number;
  component_id: string;
  event_code: string;
  state: string;
  severity: string;
  measurement: number | null;
  unit: string;
  details: Record<string, string | number | boolean>;
};

const pageSize = 20;

export function EventTimeline({ records }: { records: EvidenceEvent[] }) {
  const [code, setCode] = useState("STATE_TRANSITION");
  const [component, setComponent] = useState("all");
  const [page, setPage] = useState(0);
  const matches = records.filter(record => (code === "all" || record.event_code === code)
    && (component === "all" || record.component_id === component));
  const pageCount = Math.max(1, Math.ceil(matches.length / pageSize));
  const visible = matches.slice(page * pageSize, (page + 1) * pageSize);

  return <section className="timeline" aria-labelledby="timeline-title">
    <h3 id="timeline-title">Event timeline</h3>
    <p>Recorded delivery times in simulation milliseconds. Expand a record to inspect its evidence ID and acquisition details. Filters preserve recorded order.</p>
    <div className="timeline-filters">
      <label>Event type<select value={code} onChange={event => { setCode(event.target.value); setPage(0); }}>
        <option value="STATE_TRANSITION">State transitions</option>
        <option value="SENSOR_SAMPLE">Sensor samples</option>
        <option value="POWER_SAMPLE">Power samples</option>
        <option value="all">All events</option>
      </select></label>
      <label>Component<select value={component} onChange={event => { setComponent(event.target.value); setPage(0); }}>
        <option value="all">All components</option>
        <option value="subsystem">Subsystem</option>
        <option value="sensor-a">Sensor A</option>
        <option value="sensor-b">Sensor B</option>
        <option value="battery">Battery</option>
      </select></label>
    </div>
    <p role="status">{matches.length} matching events. Page {page + 1} of {pageCount}.</p>
    {visible.length === 0 ? <p>No events match these filters.</p> : <div className="timeline-scroll">
      <table>
        <caption className="visually-hidden">Saved event evidence, up to 20 records per page</caption>
        <thead><tr><th scope="col">Time (ms)</th><th scope="col">Component</th>
          <th scope="col">Event / state</th><th scope="col">Evidence</th></tr></thead>
        <tbody>{visible.map(record => <tr key={record.event_id}>
          <td>{record.sim_time_ms}</td><td>{record.component_id}</td>
          <td>{record.event_code}<br /><strong>{record.state}</strong></td>
          <td><details><summary>Record {record.sequence}</summary>
            <dl className="event-evidence">
              <div><dt>Event ID</dt><dd className="identity">{record.event_id}</dd></div>
              <div><dt>Severity</dt><dd>{record.severity}</dd></div>
              <div><dt>Measurement</dt><dd>{record.measurement === null ? "None" : `${record.measurement} ${record.unit}`}</dd></div>
            </dl><pre>{JSON.stringify(record.details, null, 2)}</pre>
          </details></td>
        </tr>)}</tbody>
      </table>
    </div>}
    <nav className="timeline-pages" aria-label="Timeline pages">
      <button type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous events</button>
      <button type="button" disabled={page + 1 >= pageCount} onClick={() => setPage(page + 1)}>Next events</button>
    </nav>
  </section>;
}
