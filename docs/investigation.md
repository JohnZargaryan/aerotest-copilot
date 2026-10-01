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
chatbot. Run comparison, scripted investigations and UI integration remain next.
Tests verify no pagination omissions, combined inclusive filters, report-citation
resolution, saved-record preservation and rejection of invalid/unbounded queries.
