# Browser evidence timeline

After a simulation completes and is saved, the browser displays an Event timeline.
It defaults to state transitions. Event type and component filters combine, preserve
saved record order and reset pagination. A new saved execution resets both filters
and the page. Pages show at most 20 records; previous/next controls are disabled at
the boundaries, and an empty filter result is explicit.

Times are recorded delivery simulation times in milliseconds. Expand a record to
see its original event ID, severity, measurement/unit and structured details.
For delayed sensor deliveries, sample_time_ms is acquisition time and can differ
from the table's delivery time. Null measurements are shown as None. Details render
as text, not executable HTML or instructions. Sequence numbers remain visible in
the disclosure label and establish ordering within a tick.

The timeline reads the already returned saved result; filtering does not rerun a
simulation, rewrite evidence or call investigation tools. Pagination bounds rendered
rows, not the API response size; validated executions are already limited to 4000
records. The surrounding saved execution ID scopes every displayed evidence ID.
No requirement verdict is inferred from a recorded state. Charts and investigation
views remain planned. Tables scroll horizontally on narrow screens; the mobile
layout has not yet received visual verification.
