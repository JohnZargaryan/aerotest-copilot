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
