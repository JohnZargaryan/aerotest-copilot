import { useId } from "react";
import type { EvidenceEvent } from "./EventTimeline";
import { coordinates, samples, sensorRange } from "./telemetry";

type Series = { name: string; color: string; diamond?: boolean;
  points: ReturnType<typeof samples> };

function Plot({ title, unit, series, range, durationMs }: {
  title: string; unit: string; series: Series[]; range: [number, number]; durationMs: number;
}) {
  const id = useId();
  const [low, high] = range;
  const count = series.reduce((sum, item) => sum + item.points.length, 0);
  return <figure className="telemetry-plot">
    <figcaption>{title}</figcaption>
    <p>{count} recorded samples. Vertical axis: {unit}, {low.toFixed(1)} to {high.toFixed(1)}.</p>
    {count === 0 ? <p>No matching telemetry samples.</p> : <svg viewBox="0 0 640 230"
      role="img" aria-labelledby={id}>
      <title id={id}>{title}: recorded sample values over delivery time, from 0 to {durationMs / 1000} seconds. Missing samples are not filled or joined.</title>
      {[low, (low + high) / 2, high].map(value => {
        const { y } = coordinates(0, value, durationMs, low, high);
        return <g key={value}><line x1="56" x2="620" y1={y} y2={y} stroke="#d4dcd6" />
          <text x="48" y={y + 4} textAnchor="end">{value.toFixed(1)}</text></g>;
      })}
      <line x1="56" x2="56" y1="20" y2="190" stroke="#72837c" />
      <text x="56" y="210">0 s</text>
      <text x="620" y="210" textAnchor="end">{durationMs / 1000} s</text>
      <text x="338" y="227" textAnchor="middle">Delivery simulation time (s)</text>
      {series.map(item => <g key={item.name} fill={item.color}>
        {item.points.map(({ event, value }) => {
          const { x, y } = coordinates(event.sim_time_ms, value, durationMs, low, high);
          const tooltip = `${item.name}: ${value.toFixed(3)} ${unit} at ${event.sim_time_ms} ms; ${event.event_id}`;
          return item.diamond ? <path key={event.event_id}
            d={`M ${x} ${y - 2.5} l 2.5 2.5 l -2.5 2.5 l -2.5 -2.5 Z`}><title>{tooltip}</title></path>
            : <circle key={event.event_id} cx={x} cy={y} r="1.8"><title>{tooltip}</title></circle>;
        })}
      </g>)}
    </svg>}
    <ul className="chart-legend">{series.map(item => <li key={item.name}>
      <span style={{ color: item.color }}>{item.diamond ? "Diamond" : "Circle"}</span>{item.name}
      <span>{item.points.length} samples</span></li>)}</ul>
  </figure>;
}

export function TelemetryCharts({ records, durationMs }: {
  records: EvidenceEvent[]; durationMs: number;
}) {
  const a = samples(records, "sensor-a", "SENSOR_SAMPLE", "mdegC", 1000);
  const b = samples(records, "sensor-b", "SENSOR_SAMPLE", "mdegC", 1000);
  const battery = samples(records, "battery", "POWER_SAMPLE", "basis_points", 100);
  return <section className="telemetry" aria-labelledby="telemetry-title">
    <h3 id="telemetry-title">Telemetry charts</h3>
    <p>Each mark is a recorded sample at its delivery time. Missing samples are left empty; no lines interpolate between them. Use the event timeline for exact values and acquisition times.</p>
    <Plot title="Sensor measurements" unit="degrees C" durationMs={durationMs}
      range={sensorRange([...a, ...b].map(point => point.value))}
      series={[{ name: "Sensor A", color: "#326a57", points: a },
        { name: "Sensor B", color: "#995110", diamond: true, points: b }]} />
    <Plot title="Battery remaining" unit="%" durationMs={durationMs} range={[0, 100]}
      series={[{ name: "Battery", color: "#315e91", points: battery }]} />
    <p>Sensor axes fit the recorded range; battery uses a fixed 0-100% scale. Charts describe observations, not requirement verdicts.</p>
  </section>;
}
