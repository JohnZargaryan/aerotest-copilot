# Interview guide

## Honest project description today

"I am building an AI-assisted educational simulation/test investigation project.
The first checkpoint establishes C++/Python configuration contracts and automated
checks. I use AI assistance and am learning to explain and modify the code. The
simulation, runtime verification and chatbot are not implemented yet."

Do not describe this as flight software, a validated physical model, professional
C++ experience, or evidence that a particular employer must consider you eligible.

## Checkpoint 1: why this design?

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

## Practice before the next checkpoint

1. Explain why 42, "42", true and 42.0 are treated differently as seeds.
2. Trace a request with duration_ms=1050 through Python and C++.
3. Explain why validation success does not mean a simulation requirement passed.
4. Small exercise: add a shared acceptance case for a null scenario, predict both
   results, then run the checks. Record your own explanation in your own words.
5. Find the value/reference distinction in `parse_config` and `to_json`.

## Future sections

Add state-machine concepts, deterministic replay, checker failures, safe subprocess
execution, SQLite design, evidence validation, actual agent evaluation and deployment
tradeoffs as they are built and tested. Never invent a debugging story or result.
