# Local run API

POST /api/v1/runs accepts SimulationConfig, waits for the bounded simulator,
validates and stores a completed execution, then returns HTTP 201 with
StoredExecution and a Location header. GET /api/v1/runs/{execution_id} returns
the same saved response. The ID is the storage UUID, not the deterministic run ID.
Responses include execution_id, created_at and result (configuration and records).
The committed stored-execution schema is checked alongside existing contracts.

Start the API using the README command bound to 127.0.0.1. Example in PowerShell:

```powershell
$execution = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/runs -ContentType application/json -Body '{"scenario_id":"healthy-baseline"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/runs/$($execution.execution_id)"
```

The default database is repository-local runtime/aerotest.sqlite and is ignored
by Git. create_app(database_path) allows application-controlled paths for tests.
No database is created at module import. Health advertises implemented capability,
not executable/database readiness. Failed runs do not create completed records.
Repeated POST requests intentionally create distinct executions; there is no
idempotency key or background job queue.

Errors use FastAPI's detail envelope. Invalid configurations/UUIDs return 422;
unknown execution UUIDs return 404 RUN_NOT_FOUND. TIMEOUT returns 504; START_FAILED
returns 503; other runner failures return 502. Storage failures return 503
STORAGE_UNAVAILABLE without internal paths or SQLite messages. At most two POST
operations run per application instance; excess attempts return 503 RUN_CAPACITY.
Slots are released on success and failure. This limit is per process, not global.

Synchronous endpoints run in worker threads. Each execution owns a new asyncio
loop so Windows subprocess support does not depend on the server's loop choice.
SQLite calls also stay off the server event loop. A client disconnect does not
cancel the worker: a bounded run may still finish and be saved. This local demo
has no authentication or deployment hardening; public deployment is not part of
this feature. No frontend controls, history listing or requirement verdicts are
added.

Tests exercise real C++ execution and SQLite round trips across app recreation for
all scenarios, validation/missing IDs, error mapping, storage failure sanitization,
capacity rejection and releasing slots after failures.
