# Interactive recorded-run explorer

The public explorer is a browser-only entry point built from the same charts,
timeline, check-report and investigation components as the local application.
It loads actual C++ outputs and Python reports from static JSON files. There is
no simulation API, database service, model call, free-form chat or online run
generation in this mode. New executions still require the local application.

## Recordings and provenance

Four scenarios use seed 42, duration 30000 ms and fixed 100 ms ticks. Each bundle
contains its completed execution, UTC capture time, source revision, scoped check
report and five scripted explanations (all assessed requirements and each of the
four individual focuses). Original event records and identities are retained.
The manifest records file sizes and SHA-256 hashes. Runtime/evaluation answer
keys are never used by the exporter or public explorer.

The committed captures were generated from simulator/checker revision
`8f286b07b88ff6a636a0324f92c2a573fc0baadb`. Capture times and UUIDs represent
actual exports, not the date a visitor opens the page. Regenerating snapshots
creates fresh UUIDs and UTC capture times; seeded simulation evidence repeats.

## Reproduce and build

With the simulator and Python environment set up as described in the README:

```powershell
.venv/Scripts/python.exe scripts/export_recorded_demo.py
cd frontend
npm test
npm run build
```

Serve `frontend/dist` over HTTP and open `demo.html`. The normal local API entry
remains `index.html`. Relative assets allow the recorded demo to be hosted under
a subdirectory. For a recorded-only publication, copy `demo.html`, `recorded/`,
the `assets/demo-*.js` entry and its shared `assets/RequirementResults-*` JS/CSS
dependencies. Do not publish the local-app index as the recorded demo.

The portfolio embeds this build at `/projects/aerotest` and provides a full-page
link at `/demos/aerotest/demo.html`. The public demo introduces no new backend,
external API credential, storage binding or paid service.

## Validation and limits

- Frontend tests verify all four manifest hashes and bundle identities, validate
  every focus/citation, and reject foreign executions, altered evidence and
  report/explanation disagreement.
- Python tests revalidate the saved simulator contract and reproduce every report
  and all 20 scripted explanations using the runtime checkers/investigator.
- A browser review exercised all four scenarios, selected AT-REQ-001 with 13
  original sensor citations, and confirmed state/report reset on scenario changes.
- At 390 px, charts remained keyboard-scrollable and document content did not
  overflow. Filtering sensor B produced 300 events; pagination reached page 2 of
  15. Desktop review used the default 1280 px viewport. The case-study iframe and
  full-page entry were served from the real portfolio subpath.

These observations are bounded to one Windows embedded browser. They are not a
screen-reader audit, physical-device test or safety certification. PASS assesses
only observed obligations; absent fault triggers can be INCONCLUSIVE. Requirements
004/005 remain unassessed by runtime checkers. The fictional civilian subsystem
is not flight software or a validated physical model.

Learning exercise: choose missing messages, inspect its freshness check, then
find the cited delivery/acquisition times in the original record. Explain why
healthy baseline is inconclusive for a fault that was never exercised.
