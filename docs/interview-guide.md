# Interview guide

## Project summary

"I am building an AI-assisted educational simulation/test investigation project.
The implemented core includes C++/Python configuration contracts, state transitions,
four repeatable CLI simulation scenarios, and automated checks. I use AI
assistance and am learning to explain and modify the code. Independent runtime verification, web execution and the chatbot are not implemented yet."

This is an educational simulation, not flight software or a validated physical model.

## Configuration design

- **C++ struct:** `Config` groups data; default member values document defaults.
- **Fixed-width integer:** `std::uint32_t` gives seeds a clear 0..4294967295 range.
- **Const reference:** `const nlohmann::json&` avoids copying input and prevents mutation.
- **Namespace:** `aerotest` groups project names and avoids collisions.
- **Header/source split:** the header exposes the interface; the source implements it.
- **Exceptions at a boundary:** parsing rejects invalid values; main translates errors
  to structured JSON and a nonzero exit code.
- **CMake target:** the validation library can be used by both executable and tests.
- **Independent implementations:** Python and C++ both validate; shared cases and
  subprocess comparison catch disagreements between them.

GoogleTest checks C++ directly. pytest checks API errors and real executable I/O.
This validates configuration, not simulated aircraft behavior or agent accuracy.

## Real debugging stories

1. CMake dropped a command-line definition containing the `#` in the workspace path.
   Generated a header with the path instead, then rebuilt and reran the tests.
2. The oversized-input test initially used a 65,537-character pytest parameter ID.
   That caused Windows test setup errors. Added short descriptive IDs while keeping
   the oversized payload, so the test measures input bounds rather than label size.
3. TypeScript needed Vite's client types to recognize a CSS side-effect import.
   Added `vite-env.d.ts` and repeated the frontend build.

## Configuration exercises

1. Explain why 42, "42", true and 42.0 are treated differently as seeds.
2. Trace a request with duration_ms=1050 through Python and C++.
3. Explain why validation success does not mean a simulation requirement passed.
4. Small exercise: add a shared acceptance case for a null scenario, predict both
   results, then run the checks. Record your own explanation in your own words.
5. Find the value/reference distinction in `parse_config` and `to_json`.

## Future sections

Add checker failures, safe subprocess
execution, SQLite design, evidence validation, actual agent evaluation and deployment
tradeoffs as they are built and tested.

## 2026-09-15: state-transition core

Built with Codex assistance: a scoped `enum class State`, a value-type input
struct, and a pure function returning the next state. Separating policy from
measurement/timing logic makes conflicting signals easy to test without a clock.
A scoped enum prevents accidental implicit integer conversion; a defensive default
rejects invalid values created by an explicit cast.

Verified with ten new GoogleTest tests, including an adjacency-table check of
all 192 state/signal combinations. Existing validation tests still pass. The
function is not connected to the CLI or a simulator yet. Requirements involving
milliseconds, sensor thresholds and battery levels remain unfinished.

Exercise: predict OFF -> STARTUP -> SAFE -> SAFE
-> SHUTDOWN for start, startup-complete plus safe, all-clear, and shutdown signals.
Explain why clearing safe_required does not return SAFE to NOMINAL. Then add a
sequence test showing DEGRADED -> SAFE -> SHUTDOWN, and explain each transition.


## Deterministic baseline

Built with Codex assistance: the CLI advances a simulated clock in 100 ms steps.
It does not sleep. Each run owns its pseudorandom generator state, so prior runs
cannot change its readings. Explicit integer arithmetic and JSON output with LF
line endings make the recorded output reproducible across supported platforms.
The noise is bounded educational data, not a validated sensor model.

A run ID encodes simulator version and normalized configuration. An event adds
its sequence number. Identical configurations intentionally share identities;
a future database execution ID can distinguish separate invocations without
changing replay evidence. Default and explicitly equivalent settings match.

Exercise (to do yourself):
1. Run the README baseline command twice and compare the outputs.
2. Change seed 42 to 43; inspect the run ID and first sensor reading.
3. Explain why 30 seconds of simulated time completes without a 30-second wait.
4. Explain why a 1,000 ms run shuts down without first entering NOMINAL.
5. Describe why reproducibility alone does not establish physical correctness
   or demonstrate correct fault handling.


## Sensor disagreement exercise

Implemented with Codex assistance. Explain why the detector reads measurements
rather than the selected scenario name. Predict the result at differences 5000
and 5001 mdegC, then at 400 and 500 ms elapsed. Explain how one fresh agreeing
sample or stale sample interrupts persistence. Run sensor-disagreement with
2500 and 2600 ms durations: why does only the latter enter DEGRADED? Finally,
inspect readings after 4000 ms and explain why the state does not recover.


## Sample freshness exercise

Implemented with Codex assistance. Run missing-messages for 5000 ms and find the
sensor-b record delivered at 2400. Explain why its age is 400 ms and why receipt
does not make it fresh. Trace the last sensor-a sample to the SAFE transition at
3300. Compare runs ending at 3300 and 3400; explain shutdown priority. Finally,
explain why SAFE stays latched when both sensors resume delivery at 4000.


## Battery threshold exercise

Implemented with Codex assistance. Run battery-degradation with durations 8100,
8200, 9100 and 9200 ms. Predict which transitions appear before running it.
Explain why exact 20% and 10% do not cross their respective thresholds, why both
signals are true below 10%, and why SAFE wins. Inspect the zero-power readings
at 10000 ms and explain why this accelerated model does not validate real hardware.


## Python process boundary exercise

Implemented with Codex assistance. Explain why stdout and stderr must be drained
at the same time, why a timeout alone does not bound output memory, and why a
killed child must be waited for. Run the timeout and cancellation tests and locate
the assertion that the process exited. Explain why valid event JSON does not
prove that a simulation requirement passed. Trace a changed event ID through
result validation and identify the INVALID_RESULT error.
