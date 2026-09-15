# Interview guide

## Project summary

"I am building an AI-assisted educational simulation/test investigation project.
The implemented core includes C++/Python configuration contracts, state transitions,
and automated checks. I use AI assistance and am learning to explain and modify the code. The
simulation, runtime verification and chatbot are not implemented yet."

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

Add state-machine concepts, deterministic replay, checker failures, safe subprocess
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
