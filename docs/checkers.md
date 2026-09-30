# Independent transition-edge checker

check_transition_edges(result) in aerotest.checkers inspects completed execution
evidence using a Python adjacency table, without calling or importing the C++
transition function. It does not select expected behavior from the scenario name
or an evaluation answer key. The runner's structural decoder is reused only for
version, identity, ordering and completion validation.

The CheckResult carries requirement_id AT-REQ-006, status, reason, evidence_ids
and an explicit scope. PASS means recorded edges and record states conform to
the adjacency policy. FAIL cites the first forbidden/disconnected edge, conflicting
transition destination or unrecorded state change. INCONCLUSIVE means structural,
startup or endpoint evidence is missing/invalid. PASS includes the transition IDs;
all citations resolve within the supplied trace. Results are local Python values,
not yet persisted or returned by the run API.

Scope is deliberately partial: this does not check when a fault should trigger,
whether measurements are complete, whether a transition was justified by sensor
or power data, or whether a physical model is correct. An edge permitted by the
policy can still occur at the wrong time. Do not present this PASS as full
AT-REQ-006 compliance or as a verdict for other requirements. The catalog remains
partially_implemented until the remaining checks are available.

Tests use all four real simulator scenarios, the minimum-duration baseline and
copies with defective transitions/state labels. Missing final evidence and missing
transition endpoints must yield INCONCLUSIVE. Fault-trigger and timing checkers,
aggregate results and API/UI integration remain planned.


## Battery response obligations

check_battery_response independently reads measured battery values and states at
all active ticks. It requires one fresh POWER_SAMPLE in basis_points per tick,
valid values 0..10000, and complete structural execution evidence. Missing,
duplicate, wrong-unit or stale power evidence produces INCONCLUSIVE.

After startup (1000 ms), values below 2000 require DEGRADED or SAFE on that same
tick. Values below 1000 require SAFE, which must remain through subsequent power
samples even if power recovers. Exact boundaries do not impose the stricter state.
Shutdown has no sample and takes precedence. Failures cite the violating power
record and, when relevant, the original SAFE-triggering sample. PASS cites the
first low-power obligation, SAFE trigger if observed, and final power record.
No eligible low-power condition produces INCONCLUSIVE, not a vacuous PASS.

This AT-REQ-003 result is scoped to obligations actually observed; a run exercising
only degradation does not establish SAFE coverage. It does not reject early SAFE
caused by another fault, independently validate physical power values, or establish
transition-edge consistency. Use the separate edge checker for state-event
consistency. Checkers do not consult scenario schedules or C++ detector code.
Results are not yet persisted or exposed by the API. Sensor disagreement/freshness
checks and aggregate coverage/results remain planned.


## Sensor freshness obligations

check_freshness_response reconstructs the latest sensor-a and sensor-b acquisitions
from delivered SENSOR_SAMPLE records without consulting the scenario schedule.
Age >300 ms is stale; equality remains fresh. After startup, one stale sensor
requires DEGRADED or SAFE on that tick; both require SAFE, which remains latched
when delivery resumes. Delayed messages retain acquisition time, not receipt time.
Shutdown is excluded from active ticks and therefore takes precedence.

The checker requires both initial sensors, valid millidegree measurements and
nonfuture, nondecreasing acquisition times on ticks. Duplicate deliveries per
sensor/tick are ambiguous. A battery POWER_SAMPLE is the per-tick state witness,
and all records on that tick must agree on state. Missing/ambiguous evidence is
INCONCLUSIVE. No observed eligible staleness is also INCONCLUSIVE. Failures cite
last sensor deliveries and the violating state witness; SAFE failures also cite
the triggering evidence. PASS cites first staleness and dual-stale evidence if any.

Scope: assumes the delivery log is complete, so absence of a sensor record means
no delivery. It cannot distinguish dropped messages from silently omitted log
records, verify physical measurements or prove unexercised dual-stale coverage.
State-edge correctness remains the separate edge check. Results are still local
Python values; persistent-disagreement checks and aggregate/API results remain next.


## Persistent disagreement obligations

check_disagreement_response reconstructs both latest sensor readings from the
same validated delivery/state evidence conventions as the freshness checker.
When both ages are <=300 ms and absolute difference is >5000 mdegC, persistence
begins. Agreement (including equality) or either stale reading resets it. At
500 ms elapsed, after startup, the recorded state must be DEGRADED or SAFE on
that tick. Shutdown has no active tick. No eligible sustained condition returns
INCONCLUSIVE; malformed or missing evidence also returns INCONCLUSIVE.

Citations include sensor events spanning the first 500 ms of the qualifying
interval and the state witness. A legal earlier DEGRADED/SAFE state is permitted
because other faults can justify it. This is an observed obligation check, not
an exclusivity check or a complete physical validation. State latching and edge
consistency remain the separate edge check. Delivery-log completeness is assumed.
The checker does not use scenario schedules or simulator detector code.

Tests cover positive and negative differences, exact 5000 versus 5001 mdegC,
the first eligible response, agreement/staleness resets, shutdown before detection,
missing initial samples and real-scenario citations. Aggregate results and API
integration are the next step; no checker result is currently persisted.


## Aggregate report API

GET /api/v1/runs/{execution_id}/checks computes a versioned CheckReport from saved
execution evidence. It neither reruns the simulator nor changes the saved record.
The report includes schema_version 1.0, checker_version 0.1.0, execution/run IDs,
all four scoped checks and unassessed requirements AT-REQ-004/005. Configuration
validation and replay have development tests, but are not runtime report verdicts.
No overall PASS is emitted. INCONCLUSIVE remains explicit for unexercised cases;
an edge-only PASS is not full AT-REQ-006 compliance. Every citation is checked
against the source record IDs before returning a report.

Results are computed on demand, not persisted snapshots. Future checker changes
must update checker_version. Missing executions return 404, malformed UUIDs 422,
and storage errors 503 as for GET run. An invalid generated citation returns a
sanitized 500 CHECK_REPORT_INVALID. OpenAPI and the committed check-report schema
describe the response. Aggregate reporting does not expand any checker's scope.
