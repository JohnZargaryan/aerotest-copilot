# State machine: transition core and healthy-baseline timing

`simulator/include/aerotest/state_machine.hpp` exposes `State`, `TransitionSignals`,
and `next_state(current, signals)`. The function has no clock, I/O or hidden state.
It consumes five booleans: start_requested, startup_complete, degradation_required,
safe_required, and shutdown_requested. The healthy-baseline loop computes start,
startup-complete and shutdown signals from integer simulation ticks. Fault signals
and threshold detection remain planned.

OFF only responds to start_requested and enters STARTUP, never skipping startup.
SHUTDOWN is terminal regardless of input. Active states honor shutdown first.
STARTUP holds until startup_complete, then applies SAFE before DEGRADED before
NOMINAL. DEGRADED and SAFE latch. Unrecognized enum values throw invalid_argument.
Signals irrelevant to a state are ignored. A caller owns the state between ticks.

Tests cover every documented edge and hold, startup gating, competing signals,
and all 192 state/signal combinations against an independent adjacency table.
Baseline integration tests additionally verify startup at 0 ms, nominal at 1000 ms,
and shutdown at the configured duration. Fault timing is not implemented yet.

## Timing and measurement design (fault conditions remain planned)

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
See docs/baseline.md for the implemented noise algorithm. Fault schedules remain planned.
