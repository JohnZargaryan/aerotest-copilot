# Development log

## 2026-09-14 — Foundation

Implemented with OpenAI Codex assistance. No paid API calls were made.

### Built

- New independent Git repository; existing sibling projects untouched.
- Portable checksum-verified Windows C++ toolkit and a project Python environment.
- Strict C++/Python config validation, 20 shared input cases, versioned public schemas.
- FastAPI health and validation endpoints, C++ validation CLI, React foundation shell.
- Measurable requirements catalog with unimplemented behavior explicitly planned.
- Setup/verification scripts, pinned dependencies, and basic CI configuration.
- Architecture, roadmap, portfolio plan and learning notes.

### Verified locally

`scripts/verify.ps1` completed successfully on Windows:
- 2 GoogleTest tests, including a loop over 20 shared acceptance cases.
- 46 pytest cases including real C++ subprocess output, invalid inputs and API behavior.
- Ruff lint, committed-schema freshness, and pip dependency compatibility.
- TypeScript checking and Vite production build.
- Reinstalled locked dependencies into a fresh Python environment: all 46 tests passed.
- Reinstalled npm dependencies with `npm ci --ignore-scripts` and rebuilt successfully.
- Inspected the real browser page at desktop and 390 px mobile viewport widths.

Actual JUnit reports are written to ignored `artifacts/`. No simulated requirement
result or model-evaluation result is claimed. CI has not run on GitHub. Docker and
Linux clean setup have not been tested. No repository remote or public deployment exists.

### Bugs found and fixed

- A CMake compiler definition could not carry a path containing `#`; replaced it
  with a configured header and reran the C++ checks.
- A long pytest parameter ID caused Windows setup errors for oversized input;
  replaced the label with a short ID while preserving the payload.
- TypeScript did not recognize a CSS import; added Vite client type declarations.
- Browser testing caught a blank Vite development page in a path containing `#`.
  Added a build-and-preview fallback so the existing project location is usable.
- A clean npm reinstall initially failed because the running preview held a native
  dependency open. Stopped that preview, repeated installation, and rebuilt successfully.

### Known limitations

Third-party TestClient deprecation warnings remain visible. The preview fallback
requires rebuilding and refreshing after edits. No persistence, scenarios, state machine or agent
exists yet. Foundation validation success is not simulation verification.

### Learning notes

Read the first section of docs/interview-guide.md. Explain strict input types,
the header/source separation, and why a configuration check cannot demonstrate
correct fault handling.

### Follow-up work

Implement only the state enum, transition function and boundary tests from
docs/state-machine.md. Then commit verified changes and explain the design.

## 2026-09-15 - State-transition core

Implemented with OpenAI Codex assistance. Added the scoped
State enum, TransitionSignals value type, and pure next_state function. The policy
enforces explicit startup, startup-completion gating, SAFE priority over DEGRADED,
latched fault states, and shutdown priority. Invalid enum values are rejected.
No timers, scenario generation, telemetry or chatbot were added.

Verification: scripts/verify.ps1 passed locally on Windows: 12 GoogleTest tests
(10 new, including all 192 state/signal combinations), 46 pytest tests, Ruff,
schema freshness, pip compatibility, TypeScript and Vite build. Actual reports
are in artifacts/cpp-tests.xml and artifacts/python-tests.xml. Existing third-party
warnings remain; pytest also reported a non-fatal cache permission warning.
No hosted CI execution or runtime requirement result is claimed.

AT-REQ-006 is partially implemented: policy is tested, but timed signal generation
and integration remain planned. No dependencies, paid services or API calls were
added.

Learning exercise: trace startup, SAFE latching and shutdown using the new pure
function; see docs/interview-guide.md. Planned next: deterministic healthy-baseline
execution and records.

## 2026-09-15 - Public repository

Published [JohnZargaryan/aerotest-copilot](https://github.com/JohnZargaryan/aerotest-copilot).
The initial Linux GitHub Actions run passed. No application deployment or paid
service was used.


## 2026-09-16 - Deterministic healthy-baseline simulation

Implemented with OpenAI Codex assistance. The C++ CLI now runs the healthy
baseline with a simulated integer clock, two seeded temperature sensors, battery
readings, and startup/nominal/shutdown events. Versioned records have stable run
and event identities. Unsupported fault scenarios return an explicit error.
The model is educational; no runtime requirement verdict or physical validation
is claimed. Web execution, persistence and investigations remain planned.

Verification: scripts/verify.ps1 passed on Windows: 19 GoogleTest tests and 57
pytest tests, Ruff, schema freshness, dependency compatibility, TypeScript and
Vite build. Tests cover duration boundaries, seed extremes, raw-struct validation,
record contracts, repeatability and unsupported scenarios. A fixed output digest
checks canonical bytes; Windows stdout uses binary mode to preserve LF endings.
Linux CI will independently exercise the same digest after publication.
Existing third-party deprecation, pytest-cache permission and Vite path warnings
remain non-fatal. No new dependencies, paid services or API calls were added.

Learning exercise: run the same configuration twice and then change the seed.
Explain why the first outputs match, what changes with the seed, and why the
simulated duration does not require waiting that long. See docs/interview-guide.md.
Next capability: sensor-disagreement injection and threshold boundary tests.


## 2026-09-17 - Persistent sensor disagreement

Implemented with OpenAI Codex assistance. Simulator 0.3.0 runs a sensor-b bias
from 2000 through 3900 ms and detects sustained measured disagreement independently
of the injection schedule. Difference >5000 mdegC for 500 ms triggers DEGRADED;
equality or stale samples reset persistence. State latching and shutdown priority
are preserved. The detector's freshness input is tested, but stale-message
simulation and age calculation remain planned. No runtime PASS verdict is claimed.

Verification: scripts/verify.ps1 passed on Windows with 24 GoogleTest tests,
64 pytest tests, Ruff, schema freshness, dependency compatibility, TypeScript
and Vite build. Tests cover threshold signs, duration boundaries, timer reset,
extreme integer subtraction, bias removal, seed extremes, replay, short runs
and shutdown at the detection tick. Baseline bytes were unchanged after normalizing
the version text; the canonical snapshot now pins 0.3.0. An initial import-order
lint failure was corrected before the full successful verification. Existing
third-party deprecation, pytest cache-permission and Vite path warnings remain.
No dependencies, paid services, API calls or deployment were added.

Learning exercise: explain the 2500 versus 2600 ms run results and why DEGRADED
persists after bias removal. See docs/interview-guide.md. Next: delayed/missing
messages and freshness boundaries.


## 2026-09-18 - Delayed and missing sensor messages

Implemented with OpenAI Codex assistance. Simulator 0.4.0 adds a fixed bounded
missing-message scenario, acquisition-time freshness checks, single-sensor
DEGRADED and dual-sensor SAFE transitions. Delayed delivery retains the original
sample timestamp and value. Dropouts produce no fabricated sensor samples.
Freshness is evaluated independently of the scenario schedule and stale samples
reset disagreement persistence. Battery faults and runtime verdicts remain planned.

Verification: scripts/verify.ps1 passed on Windows with 25 GoogleTest tests,
71 pytest tests, Ruff, schema freshness, dependency compatibility, TypeScript
and Vite build. Tests cover the inclusive 300 ms boundary, future timestamps,
delayed values and acquisition times, missing records, extreme seeds, replay,
shutdown priority and SAFE latching after delivery resumes. Baseline canonical
bytes match the prior version after normalizing only version text. Existing
third-party deprecation, pytest cache-permission and Vite path warnings remain.
No dependencies, paid services, API calls or deployments were added.

Learning exercise: explain why the 2400 ms delivery is stale and trace the SAFE
transition at 3300 ms; see docs/interview-guide.md. Next: battery degradation
and precedence boundaries.


## 2026-09-20 - Battery degradation and priority boundaries

Implemented with OpenAI Codex assistance. Simulator 0.5.0 adds accelerated battery
discharge, strict 20%/10% detection, and zero clamping. All four declared scenarios
now execute. Sensor readings and normal power behavior in other scenarios are
preserved. SAFE wins when low-power signals overlap; shutdown wins at threshold
crossings. This educational signal is not a physical battery model.

Verification: scripts/verify.ps1 passed on Windows with 27 GoogleTest tests,
80 pytest tests, Ruff, schema freshness, dependency compatibility, TypeScript
and Vite build. Tests cover exact and adjacent thresholds, signal priority,
short runs, maximum-duration clamping, sensor preservation, extreme seeds and
replay. The baseline byte snapshot matches its predecessor after normalizing
only version text. Existing third-party deprecation and Vite path warnings remain.
No dependencies, paid services, API calls or deployments were added.

Learning exercise: predict transitions for runs ending at 8100 versus 8200 ms
and 9100 versus 9200 ms; see docs/interview-guide.md. Next: bounded Python process
execution with clean timeout and failure handling. Independent requirement
verdicts and web execution remain planned.
