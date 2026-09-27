"""Evidence-based checks independent of the C++ transition implementation."""

from dataclasses import dataclass
from typing import Literal

from aerotest.runner import RunnerError, SimulationResult, _decode


@dataclass(frozen=True)
class CheckResult:
    requirement_id: str
    status: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    reason: str
    evidence_ids: tuple[str, ...]
    scope: str = "transition edges and state consistency; excludes trigger timing"


def check_transition_edges(result: SimulationResult) -> CheckResult:
    def verdict(status, reason, *evidence):
        return CheckResult("AT-REQ-006", status, reason, tuple(evidence))

    try:
        trace = _decode(result.model_dump_json().encode(), result.config)
    except (RunnerError, ValueError):
        return verdict("INCONCLUSIVE", "Incomplete or structurally invalid execution evidence.")
    allowed = {
        "OFF": {"STARTUP"},
        "STARTUP": {"NOMINAL", "DEGRADED", "SAFE", "SHUTDOWN"},
        "NOMINAL": {"DEGRADED", "SAFE", "SHUTDOWN"},
        "DEGRADED": {"SAFE", "SHUTDOWN"},
        "SAFE": {"SHUTDOWN"},
        "SHUTDOWN": set(),
    }
    current = "OFF"
    transitions = []
    for record in trace.records:
        if record.event_code == "STATE_TRANSITION":
            before = record.details.get("from_state")
            after = record.details.get("to_state")
            if before not in allowed or after not in allowed:
                return verdict("INCONCLUSIVE", "Transition endpoints are missing or unknown.",
                               record.event_id)
            if before != current or after not in allowed[current]:
                return verdict("FAIL", f"Forbidden or disconnected edge {before} -> {after}.",
                               record.event_id)
            if record.state != after:
                return verdict("FAIL", "Transition state disagrees with its destination.",
                               record.event_id)
            current = after
            transitions.append(record.event_id)
        elif record.state != current:
            return verdict("FAIL", "Record state changes without a matching transition.",
                           record.event_id)
    first = trace.records[0]
    if (not transitions or first.event_code != "STATE_TRANSITION"
            or first.sim_time_ms != 0 or first.state != "STARTUP"):
        return verdict("INCONCLUSIVE", "Initial startup evidence is missing.")
    return verdict("PASS", "Recorded edges and states obey the transition policy.", *transitions)


def check_battery_response(result: SimulationResult) -> CheckResult:
    """Check low-power obligations, not whether other faults justify an early state."""
    def verdict(status, reason, *evidence):
        return CheckResult("AT-REQ-003", status, reason, tuple(evidence),
                           "low-power response and SAFE latching; excludes other fault causes")

    try:
        trace = _decode(result.model_dump_json().encode(), result.config)
    except (RunnerError, ValueError):
        return verdict("INCONCLUSIVE", "Incomplete or structurally invalid execution evidence.")
    power = {}
    for record in trace.records:
        if record.component_id != "battery":
            continue
        time = record.sim_time_ms
        acquired = record.details.get("sample_time_ms")
        if (time in power or record.event_code != "POWER_SAMPLE" or record.unit != "basis_points"
                or type(record.measurement) is not int or not 0 <= record.measurement <= 10000
                or type(acquired) is not int or acquired != time):
            return verdict("INCONCLUSIVE", "Ambiguous or invalid power evidence.", record.event_id)
        power[time] = record
    if sorted(power) != list(range(0, trace.config.duration_ms, trace.config.step_ms)):
        return verdict("INCONCLUSIVE", "Power evidence does not cover every active tick.")
    safe_trigger = None
    witnesses = []
    for time, record in power.items():
        if time < 1000:  # Startup gating; shutdown has no power sample.
            continue
        if record.measurement < 1000 and safe_trigger is None:
            safe_trigger = record.event_id
        requires_safe = safe_trigger is not None
        requires_degraded = record.measurement < 2000
        if requires_safe and record.state != "SAFE":
            return verdict("FAIL", f"SAFE required at {time} ms.",
                           *dict.fromkeys((safe_trigger, record.event_id)))
        if requires_degraded and record.state not in ("DEGRADED", "SAFE"):
            return verdict("FAIL", f"DEGRADED or SAFE required at {time} ms.", record.event_id)
        if (requires_safe or requires_degraded) and len(witnesses) < 1:
            witnesses.append(record.event_id)
    if not witnesses:
        return verdict("INCONCLUSIVE", "No eligible low-power condition was exercised.")
    if safe_trigger and safe_trigger not in witnesses:
        witnesses.append(safe_trigger)
    witnesses.append(power[max(power)].event_id)
    return verdict("PASS", "Observed low-power obligations and SAFE latching were satisfied.",
                   *dict.fromkeys(witnesses))
