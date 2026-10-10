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
No requirement verdict is inferred from a recorded state. Scripted investigation is available below the scoped checks. Tables scroll horizontally on narrow screens; the mobile
layout has not yet received visual verification.


## Recorded telemetry charts

Sensor measurements convert mdegC to degrees C; battery converts basis points to
percent. Only matching component/code/unit records with finite non-null measurements
are plotted. Sensor axes fit the recorded range with padding (they do not start at
zero); battery uses 0..100%. The horizontal axis spans the saved duration and uses
delivery simulation time in seconds. Every recorded sample is drawn, without
resampling, interpolation or connecting across missing intervals. Sensor A uses
circles and Sensor B diamonds with distinct colors and a textual legend.

SVG titles describe the chart; sample titles provide exact time, value and evidence
ID on pointer hover. The event timeline provides keyboard-accessible exact values
and acquisition details. Overlapping marks can obscure individual values, and
changing sensor ranges limits visual comparisons across different executions.
Charts are descriptive and do not infer requirements or causes. The five telemetry
unit tests run without added packages in both verification and GitHub Actions.


## Scoped requirement results

Load requirement checks retrieves the saved execution's check API report. Cards
show PASS, FAIL or INCONCLUSIVE, the original reason and scope, checker version,
and explicit unassessed requirements. No overall compliance verdict is inferred.
The browser validates schema, execution/evidence identity, four unique supported
checks, statuses and citation resolution against the current saved records.
Malformed or mismatched reports are rejected rather than partially displayed.

Expand evidence references for original IDs, delivery time, component and state.
At most 20 references per check are displayed, with explicit truncation; the check
API retains the full report. Requests have a 15-second timeout, prevent overlap
and are cancelled when a new execution replaces the panel. A failed reload retains
the previous report alongside an error. New executions reset the report. Scripted
investigation is documented in scripted-investigation.md; mobile visual verification remains planned.
