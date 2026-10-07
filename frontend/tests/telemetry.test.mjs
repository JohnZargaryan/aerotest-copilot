import test from "node:test";
import assert from "node:assert/strict";
import { samples, sensorRange, coordinates } from "../src/telemetry.ts";
const event = (time, measurement, extra = {}) => ({ sim_time_ms: time, measurement,
  component_id: "sensor-b", event_code: "SENSOR_SAMPLE", unit: "mdegC", ...extra });
test("unit conversion preserves delayed delivery and missing intervals", () => {
  const result = samples([event(1900, 20000), event(2400, 19963,
    { details: { sample_time_ms: 2000 } }), event(4000, 26000)],
    "sensor-b", "SENSOR_SAMPLE", "mdegC", 1000);
  assert.deepEqual(result.map(p => p.value), [20, 19.963, 26]);
  assert.deepEqual(result.map(p => p.event.sim_time_ms), [1900, 2400, 4000]);
  assert.equal(result[1].event.details.sample_time_ms, 2000);
});
test("unrelated and invalid measurements are excluded", () => {
  assert.equal(samples([event(0, 20000), event(0, null), event(0, Infinity),
    event(0, 1, { unit: "none" }), event(0, 1, { component_id: "battery" }),
    event(0, 1, { event_code: "STATE_TRANSITION" })],
    "sensor-b", "SENSOR_SAMPLE", "mdegC", 1000).length, 1);
});
test("battery basis points convert to percentages at exact boundaries", () => {
  const records = [10000, 2000, 1000, 0].map(v => event(0, v,
    { component_id: "battery", event_code: "POWER_SAMPLE", unit: "basis_points" }));
  assert.deepEqual(samples(records, "battery", "POWER_SAMPLE", "basis_points", 100)
    .map(p => p.value), [100, 20, 10, 0]);
});
test("ranges handle empty and constant samples", () => {
  for (const values of [[], [20], [19.9, 26.1]]) {
    const [low, high] = sensorRange(values);
    assert.ok(high > low);
    assert.ok(values.every(v => v > low && v < high));
  }
});
test("axis projection places endpoints and midpoint", () => {
  assert.deepEqual(coordinates(0, 100, 30000, 0, 100), { x: 56, y: 20 });
  assert.deepEqual(coordinates(30000, 0, 30000, 0, 100), { x: 620, y: 190 });
  assert.deepEqual(coordinates(15000, 50, 30000, 0, 100), { x: 338, y: 105 });
});
