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
