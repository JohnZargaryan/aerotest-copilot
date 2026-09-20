# Battery degradation

Simulator 0.5.0 supports `scenario_id: battery-degradation`. Its illustrative
power signal begins at 10000 basis points (100%) and decreases by 100 basis
points per 100 ms tick, clamped at zero. This deliberately accelerated signal
is a software test fixture, not a physical battery model. Sensors retain their
baseline seeded noise and fresh delivery; other scenarios keep normal power.

| Time (ms) | Power | Operating state |
| --- | --- | --- |
| 8000 | 2000 (20%) | NOMINAL |
| 8100 | 1900 (19%) | DEGRADED |
| 9000 | 1000 (10%) | DEGRADED |
| 9100 | 900 (9%) | SAFE |
| 10000 onward | 0 | SAFE |

The detector reads measured power, independently of the scenario name. Exact
20% does not trigger degradation; exact 10% does not trigger SAFE. Below 10%,
both signals are true and SAFE wins. Shutdown always wins on the requested
end tick and emits no sample. Short runs can finish before either threshold.
The general state policy keeps SAFE latched until shutdown.

Tests cover adjacent integer thresholds, simultaneous signals, shutdown at each
crossing, maximum-duration zero clamping, sensor preservation, seed extremes,
record contracts and repeatable output. Versioned evidence IDs and the canonical
baseline snapshot now use 0.5.0; baseline measurements and timing are unchanged.
Independent runtime requirement verdicts and web/API execution remain planned.
