# Local execution storage

RunStore in backend/aerotest/storage.py uses Python's standard-library SQLite.
Construct it with an application-controlled local Path, then save a validated
SimulationResult or get an execution by ID. Parent directories are created on
initialization. Connections are closed after every operation; inserts are atomic
transactions with a five-second SQLite lock wait. Values use bound SQL parameters.

Each save assigns a UUID execution_id and a real UTC created_at timestamp outside
the simulator result. Replaying identical input preserves run/event identities,
while each invocation gets a distinct storage identity. The stored result is a
snapshot; changing the caller's object afterward cannot alter it. Save and read
revalidate result integrity. Missing execution IDs return None; database errors
are surfaced to the caller. No update or delete operation is exposed.

Database schema version 1 stores execution_id, created_at and result_json. Unknown
future schema versions are rejected without migration. This is a local foundation:
the create/get API connects storage to the runner (docs/run-api.md). History
listing, failed-execution records, retention, migrations and independent
requirement verdicts remain planned. Reads use
the current simulator result adapter; compatibility with future simulator versions
must be addressed before that adapter changes. The database is trusted local data,
not a format for accepting uploaded untrusted databases.

Example after awaiting run_simulation:

```python
from pathlib import Path
from aerotest.storage import RunStore

store = RunStore(Path("runtime/aerotest.sqlite"))
saved = store.save(result)
loaded = store.get(saved.execution_id)
```

Database files and runtime/ are ignored by Git. No service or credentials are
needed. Tests use temporary databases and verify round trips across reopening,
replay identity separation, input rejection, snapshots, parameterized lookup,
concurrent writes and future-version preservation.
