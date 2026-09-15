# Architecture and contracts

## Intended data flow

React UI -> FastAPI -> bounded C++ process -> independent requirement checkers
-> SQLite records -> validated investigation tools -> scripted or live agent -> UI.

Today only the UI shell, health/config API, configuration validation executable,
their contracts, and the pure C++ transition core are implemented. No run endpoint
or simulated measurements exist. The future simulator converts timing/threshold
conditions into TransitionSignals; next_state applies only the operating policy.

## Decisions

- C++20 value types, no inheritance hierarchy or unnecessary service infrastructure.
- Python owns orchestration, persistence, tool validation, and independent checkers.
- SQLite uses Python's standard library. No database server is required.
- Production FastAPI will serve the compiled frontend. Development uses Vite's
  `/api` proxy. No browser secrets; API keys stay server-side in a later checkpoint.
- Pydantic is the schema source; `scripts/export_contracts.py --check` detects drift.
  C++ validation is tested against shared configuration cases and normalized outputs.
- Integers are strict: boolean, float (even 42.0), and string coercion are rejected.
  JSON Schema cannot express lexical integer-vs-float distinctions; shared cases
  document this additional parser rule.
- Event schema v1 defines units, sequence, simulated timestamp, state, component,
  diagnostic details, run ID and event ID. It is a contract, not generated telemetry.
- Requirements catalog status means implementation status, not PASS. Runtime
  PASS/FAIL/INCONCLUSIVE results and evidence links belong to future independent checkers.

## CLI today

`aerotest-sim --validate-config` reads one JSON object from stdin through EOF.
Success: `{"schema_version":"1.0","status":"validated","config":{...}}`, exit 0.
Invalid input: `{"schema_version":"1.0","status":"error","error":{"code":"INVALID_CONFIG","message":"..."}}`, exit 2.
Only stdout contains the response. Input is capped at 64 KiB. The CLI is not yet
a simulator. The parent runner will enforce a timeout and output bound; current
subprocess use is limited to integration tests with a five-second timeout.

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

Canonical simulation IDs will derive from version and normalized input; separate
execution IDs will distinguish repeated executions without changing deterministic
output. Define the hash encoding at the simulator checkpoint.
