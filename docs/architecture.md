# Architecture and contracts

## Intended data flow

React UI -> FastAPI -> bounded C++ process -> independent requirement checkers
-> SQLite records -> validated investigation tools -> scripted or live agent -> UI.

Implemented: UI shell, health/config API, configuration validation, C++ transition
core, and healthy-baseline CLI simulation. The baseline tick loop generates
startup/shutdown signals and measurements; fault detection remains planned.
There is no API run endpoint yet. next_state applies the operating policy.

## Decisions

- C++20 value types, no inheritance hierarchy or unnecessary service infrastructure.
- Python owns orchestration, persistence, tool validation, and independent checkers.
- SQLite uses Python's standard library. No database server is required.
- Production FastAPI will serve the compiled frontend. Development uses Vite's
  `/api` proxy. No browser secrets; API keys stay server-side in the planned live adapter.
- Pydantic is the schema source; `scripts/export_contracts.py --check` detects drift.
  C++ validation is tested against shared configuration cases and normalized outputs.
- Integers are strict: boolean, float (even 42.0), and string coercion are rejected.
  JSON Schema cannot express lexical integer-vs-float distinctions; shared cases
  document this additional parser rule.
- Event schema v1 defines units, sequence, simulated timestamp, state, component,
  diagnostic details, run ID and event ID. The healthy-baseline CLI emits these records.
- Requirements catalog status means implementation status, not PASS. Runtime
  PASS/FAIL/INCONCLUSIVE results and evidence links belong to future independent checkers.

## CLI today

`aerotest-sim --validate-config` reads one JSON object from stdin through EOF.
Success: `{"schema_version":"1.0","status":"validated","config":{...}}`, exit 0.
Invalid input: `{"schema_version":"1.0","status":"error","error":{"code":"INVALID_CONFIG","message":"..."}}`, exit 2.
Only stdout contains the response. Input is capped at 64 KiB. `--run` executes the
healthy baseline and returns a versioned completed result containing normalized
config, run_id and records. Planned fault scenarios return SCENARIO_NOT_IMPLEMENTED
with exit 3. See docs/baseline.md for the exact output rules. The future parent
runner will enforce a timeout/output bound; subprocess integration tests currently
enforce five seconds. The API does not execute the CLI yet.

## API today

- `GET /api/v1/health`: foundation status; simulation/investigation availability false.
- `POST /api/v1/config/validate`: normalized config, or HTTP 422 validation details.
- `/docs`: generated API documentation.

## Future boundaries

Bound the simulator to 10 seconds and 120 seconds of simulated time; invoke with
an argument list and `shell=False`. Add output limits and clean failure persistence.
Bound agent investigations to 8 tool calls, 4 model requests, and 60 seconds.
Tools expose allowlisted queries only. Evaluation labels must not be imported,
mounted into production, or queryable through tools. Log instructions are data.

Canonical run IDs use a reversible encoding of simulator/schema version and all
normalized config fields (docs/baseline.md), without a hash dependency. Future
execution IDs will distinguish repeat executions without changing canonical output.
