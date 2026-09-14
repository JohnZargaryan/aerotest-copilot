# State machine design (not implemented yet)

All times are simulation time. Thresholds are educational assumptions.
Use 100 ms ticks including t=0. Startup ends at t=1000 ms. Initialize both
sensors with valid samples at t=0. Sample/fault updates happen before state checks.
At the requested duration, SHUTDOWN takes precedence over fault transitions.

| From | To | Condition |
| --- | --- | --- |
| OFF | STARTUP | t=0, accepted configuration |
| STARTUP | NOMINAL | t=1000 ms, neither fault condition applies |
| STARTUP | DEGRADED | t=1000 ms, degradation condition applies |
| STARTUP | SAFE | t=1000 ms, safe condition applies |
| NOMINAL | DEGRADED | disagreement >5 C continuously for 500 ms, one stale sensor, or battery <20% |
| NOMINAL / DEGRADED | SAFE | both sensors stale or battery <10% |
| STARTUP / NOMINAL / DEGRADED / SAFE | SHUTDOWN | requested duration reached |

SAFE wins over DEGRADED when conditions occur on the same tick. No automatic
recovery in v1. SHUTDOWN is terminal. Disagreement timers reset when disagreement
ends or either sample is stale. Age exactly 300 ms is fresh; the next tick is stale.
Difference exactly 5 C is not disagreement. Power exactly 20%/10% does not cross
that threshold. These boundaries require tests before behavior is claimed.

Use integer millidegrees Celsius (mdegC) and battery basis points (10000 = 100%).
Document seeded noise algorithm and fault schedules with the simulator checkpoint.
