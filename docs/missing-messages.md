# Delayed and missing messages

Simulator 0.4.0 supports `scenario_id: missing-messages`. All times below are
simulation milliseconds. Seeded sensor generation continues every tick even if
delivery fails, preserving the underlying signal sequence across scenarios.

- Sensor-b stops regular delivery at 2000 and resumes at 4000.
- Its reading acquired at 2000 is delivered once at 2400, retaining sample_time_ms=2000.
- Sensor-a stops delivery at 3000 and resumes at 4000.
- Battery samples continue normally. Samples at shutdown are never delivered.

Only delivered sensor readings produce SENSOR_SAMPLE records. Their sim_time_ms
is delivery time and details.sample_time_ms is acquisition time. Held values are
used internally without being relabeled as new samples. This is a fixed bounded
educational schedule, not a general network queue or transport model.

Freshness uses acquisition age, independently of the fault schedule. Age exactly
300 is fresh; age greater than 300 is stale. Future timestamps are rejected as
not fresh. One stale sensor requests DEGRADED; both request SAFE. Stale samples
also reset the disagreement timer. State updates follow deliveries on each tick.

Sensor-b's last ordinary sample is 1900, so it becomes stale at 2300. The delayed
sample at 2400 is already 400 ms old and does not restore freshness. Sensor-a's
last sample is 2900, so both are stale at 3300. Expected transitions are STARTUP
at 0, NOMINAL at 1000, DEGRADED at 2300, SAFE at 3300 and SHUTDOWN at the configured
duration. Short runs may end before faults; shutdown wins on matching ticks.
Fresh delivery resumes at 4000, but SAFE remains latched.

Tests check acquisition and delivery timestamps, absent records during dropouts,
seeded values, replay, state timing, shutdown boundaries and recovery latching.
Baseline output retains its measurements and timing; versioned identities and
the byte snapshot now use 0.4.0. No runtime requirement verdicts are generated.
