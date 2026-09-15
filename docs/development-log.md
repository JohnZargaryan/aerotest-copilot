# Development log

## 2026-09-14 — Foundation checkpoint

Implemented with OpenAI Codex assistance. User requested incremental daily work
and authorized downloading necessary development tools. No paid API calls were made.

### Built

- New independent Git repository; existing sibling projects untouched.
- Portable checksum-verified Windows C++ toolkit and a project Python environment.
- Strict C++/Python config validation, 20 shared input cases, versioned public schemas.
- FastAPI health and validation endpoints, C++ validation CLI, React foundation shell.
- Measurable requirements catalog with unimplemented behavior explicitly planned.
- Setup/verification scripts, pinned dependencies, and basic CI configuration.
- Architecture, backlog, portfolio plan and interview checkpoint.

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

### Learning checkpoint

Read the first section of docs/interview-guide.md. Explain strict input types,
the header/source separation, and why a configuration check cannot demonstrate
correct fault handling. The practice exercise has not been marked completed by the user.

### Next session

Implement only the state enum, transition function and boundary tests from
docs/state-machine.md. Then commit verified changes and explain the design.

## 2026-09-15 - State-transition core

Completed one daily backlog item with OpenAI Codex assistance. Added the scoped
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
added. Existing sibling projects are untouched. The session started read-only;
the authorized scoped write/build request was approved by automatic review.

Learning exercise: trace startup, SAFE latching and shutdown using the new pure
function; see docs/interview-guide.md. The user has not been credited with completing
this exercise. Next session: deterministic healthy-baseline execution and records.
