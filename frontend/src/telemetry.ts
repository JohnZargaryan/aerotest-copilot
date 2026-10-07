import type { EvidenceEvent } from "./EventTimeline";

export function samples(records: EvidenceEvent[], component: string,
                        code: string, unit: string, divisor: number) {
  return records.filter(r => r.component_id === component && r.event_code === code
    && r.unit === unit && r.measurement !== null && Number.isFinite(r.measurement))
    .map(r => ({ event: r, value: r.measurement! / divisor }));
}

export function sensorRange(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  return [Math.floor(Math.min(...values) * 10) / 10 - 0.1,
    Math.ceil(Math.max(...values) * 10) / 10 + 0.1];
}

export function coordinates(timeMs: number, value: number, durationMs: number,
                            low: number, high: number) {
  return { x: 56 + (timeMs / durationMs) * 564,
    y: 190 - ((value - low) / (high - low)) * 170 };
}
