# Local evidence investigation tools

EvidenceTools wraps the local RunStore with query_events(EventQuery) and
resolve_citations(CitationQuery). Arguments are revalidated inside each method,
including model instances constructed without validation. Tools read saved
executions and never accept SQL, shell commands, executable paths or database
paths from tool arguments. The store is configured by the application.

EventQuery selects a UUID execution, inclusive simulation interval (0..120000 ms),
optional allowlisted component/state/event-code filters, offset 0..4000 and a
limit 1..100 (default 50). Unknown fields, invalid intervals and coerced integer
values are rejected. EventPage returns execution/run identity, total matches,
next_offset and ordered events. Pagination is over the filtered record sequence;
when next_offset is None, no further matches remain. Memory use includes the
bounded saved result already validated by RunStore, not an unbounded SQL result.

CitationQuery accepts 1..20 unique event IDs (each at most 100 characters), scoped
to one execution. Lookup preserves requested order and rejects the whole query
if any citation is unresolved. A replay can share evidence IDs, so execution ID
is mandatory. Missing executions raise EXECUTION_NOT_FOUND; missing citations
raise CITATION_NOT_FOUND as LookupError. Input errors are Pydantic ValidationError.

These are local Python tools, not new HTTP endpoints, an agent dispatcher or a
chatbot. Scripted investigations and UI integration remain planned.
Tests verify no pagination omissions, combined inclusive filters, report-citation
resolution, saved-record preservation and rejection of invalid/unbounded queries.


## Saved-run comparisons

compare_runs(ComparisonQuery) takes left/right execution UUIDs and returns up to
100 differences per page (default 50), with offset 0..8000. The result includes
both configurations and execution IDs. Events match by delivery simulation tick,
component and event code, sorted by those keys. Sequence numbers and evidence
identity are excluded from content comparison because fault transitions can shift
sequence numbers. Measurement, unit, state, severity and details are compared.
Duplicate match keys raise AMBIGUOUS_EVENT_MATCH instead of guessing a pairing.
Different simulator/schema versions or step sizes raise INCOMPATIBLE_RUNS.

Each difference carries both original records; an absent side is null. Resolve
its event ID within the corresponding execution using CitationQuery. Numeric
measurement_delta is right minus left only when both measurements exist and units
match; otherwise it is null. Identical replays yield zero differences. Pagination
includes changes and one-sided events across the whole duration, including records
outside a shorter execution's duration; it does not truncate to common time.

This is a descriptive evidence comparison, not a causal analysis or an improvement
verdict. Different seeds, scenarios and durations affect interpretation; inspect
the returned configurations. Delayed samples match by delivery tick, while their
acquisition-time details remain visible. No interpolation or time alignment is
performed. The method reads at most two validated saved results and does not mutate
storage. Tests cover known sensor bias, reversal, shifted sequences, missing events,
unequal duration, replay, citations, pagination and rejected inputs.
