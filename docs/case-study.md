# AeroTest Copilot: reproducible simulation and evidence-based investigation

AeroTest Copilot connects a deterministic C++20 simulation to independent Python
checks and a React investigation interface. It explores a fictional civilian
research-aircraft subsystem through repeatable sensor and battery scenarios.

**Educational software only: not flight software or a validated physical model.**

[Recorded walkthrough](demo.md) · [Screenshots](screenshots.md) ·
[Source repository](https://github.com/JohnZargaryan/aerotest-copilot) ·
[Run locally](../README.md#start-on-windows)

![Selected scripted finding with original evidence references and recorded local tools](assets/sensor-investigation.jpg)

## The problem

A fault log is useful only if an engineer can reproduce the input, understand the
expected response and trace an explanation to the original measurements. A plausible
summary alone cannot establish that the subsystem followed its operating rules.

This project makes that investigation inspectable: choose a scenario, run it, save
its ordered records, assess observed obligations and open the evidence behind a
scoped finding. Healthy baseline, sensor disagreement, delayed/missing messages
and battery degradation provide four controlled examples.

## Architecture

The [architecture diagram and API boundaries](architecture.md) show the implemented
call relationships. C++ owns simulation ticks, measurements and state transitions.
Python owns input/output validation, bounded process execution, SQLite storage,
independent checkers and read-only evidence tools. React presents saved results,
telemetry, requirement checks and scripted explanations. Optional Docker Compose
serves the built frontend through nginx and forwards API requests to FastAPI.

A completed run is saved before checks or investigation are requested. Check reports
are computed on demand over that saved evidence; they are not simulator assertions
or separately persisted verdicts. The scripted investigator uses the same report
builder and resolves its references through typed evidence tools.

## A concrete investigation

The preserved [demo execution](assets/demo/recorded-execution.json) uses sensor
disagreement, seed 42, duration 30000 ms and 100 ms ticks. It produces 904 records.

1. At 2000 ms, sensor A reads 20043 mdegC and sensor B reads 25963 mdegC: a
   5920 mdegC disagreement, above the illustrative 5000 mdegC threshold.
2. Both sensors remain fresh and disagreement persists for 500 ms. At the first
   eligible tick, Record 77 captures NOMINAL to DEGRADED at 2500 ms.
3. The scoped disagreement-response check passes. Sensor-age and battery checks
   remain INCONCLUSIVE because their fault conditions were not exercised; transition
   check 006 passes. Requirements 004/005 remain unassessed by the runtime report.
4. The selected AT-REQ-001 explanation returns 13 original citations and records
   `build_report` followed by `resolve_citations:AT-REQ-001`.

The [saved check report](assets/demo/recorded-checks.json) and
[selected explanation](assets/demo/recorded-investigation.json) preserve these
results. DEGRADED describes simulated operating state; PASS describes the observed
response obligation. Neither is an overall compliance judgment.

## Engineering decisions and tradeoffs

| Decision | Why it helps | Boundary |
| --- | --- | --- |
| Integer ticks and explicit units | Make timing and threshold cases reproducible | Discrete illustrative behavior, not physical fidelity |
| Separate evidence and execution IDs | Repeat inputs retain evidence identity; each saved invocation gets a UUID and UTC timestamp | Reading old data still requires compatible result schemas |
| Independent Python checks | Reconstruct observed obligations from records instead of accepting a simulator PASS flag | Depend on evidence completeness and implemented checker scope |
| Bounded simulator process | Fixed executable, argument list, output caps and cleanup keep the API predictable | Trusted child process; not an arbitrary-code sandbox or full wall-time guarantee |
| SQLite completed-run snapshots | Preserve evidence without a database server | Local storage; no user accounts, retention system or distributed execution |
| Scripted narration with resolved citations | Keep explanations inspectable and usable without keys or paid model calls | No live language model, free-form chat or demonstrated causal reasoning |

## Verification and what it establishes

The recorded native verification baseline on 2026-10-12 passed 27 GoogleTest tests,
217 pytest tests and 14 frontend tests, plus lint, schema freshness, dependency
compatibility, TypeScript and the production build. These are test counts, not
coverage percentages. The [development log](development-log.md) records dates and
limits; [the hosted checks for source revision 7a53d60](https://github.com/JohnZargaryan/aerotest-copilot/actions/runs/39015239171)
also passed the foundation and container jobs.

The [scripted regression evaluation](scripted-evaluation.md) has 12 cases,
18 expected verdicts and 44 grounded returned citations. All matched the recorded
expectations. Additional seeds, shutdown boundaries and explicitly synthetic
late-response/missing-witness traces exercise PASS, FAIL and INCONCLUSIVE behavior.
The dataset was reviewed during development, so it is not a blind or external
holdout and provides no live-model accuracy estimate.

The recorded demo's complete result matched a fresh native C++ replay. Container
verification exercises all four scenarios, reports, grounded explanations and saved
executions after container replacement. The 65-second video is an edited sequence
of real browser captures with captions and a transcript; its reading holds do not
measure execution latency.

## Current limits and remaining presentation work

Live-model integration and free-form chat are disabled/unimplemented. Configuration
and replay have automated tests but no runtime 004/005 verdicts. There is no claim of
certification, physical validation, production readiness or company-specific
qualification. A [bounded mobile/keyboard review](usability-review.md) covered four
viewport sizes and keyboard flows in one Windows browser; physical devices,
screen readers and general accessibility conformance remain unverified.

The public repository, recorded demo and local setup are available. The
[$0 showcase review](hosting-review.md) recommends static presentation assets
with local execution instructions. A hosted interactive backend and portfolio-site
integration remain separate from the prepared presentation.

## Development role and interview focus

Developed with OpenAI Codex assistance. Implementation, checks, recording and this
case study used AI assistance; the repository does not claim unaided authorship.
The [interview exercises](interview-guide.md) focus on reproducing results,
explaining boundaries and tracing every cited measurement rather than memorizing
claims about the project.
