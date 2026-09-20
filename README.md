# AeroTest Copilot

**AI-assisted simulation and test investigation.**

A fictional civilian research-aircraft subsystem will provide repeatable sensor
and battery scenarios. Independent tests will check measurable requirements, and
an investigation assistant will explain results using linked evidence.

**Educational simulation only. Not flight software or a validated physical model.**

## Current status: all four CLI simulation scenarios

Implemented:
- Deterministic baseline, sensor-disagreement, missing-message and battery-degradation CLI runs with telemetry and state events.
- Low-battery thresholds with SAFE priority and nonnegative discharge telemetry.
- Sensor freshness detection with delayed-delivery evidence and missing-message faults.
- Persistent disagreement detection with strict amplitude and elapsed-time boundaries.
- Pure C++ state-transition function with startup gating, fault latching and shutdown priority.
- C++20 configuration validator with bounded JSON input and structured errors.
- Matching Pydantic contracts and FastAPI health/config-validation endpoints.
- Shared acceptance cases and real C++/Python subprocess integration tests.
- A React/TypeScript foundation screen, with future capabilities clearly labeled.
- Pinned dependencies, checksum-verified C++ dependencies, setup and verification scripts.
- Requirements catalog, architecture notes, and a GitHub Actions workflow.

**Not implemented yet:** web/API run execution, SQLite persistence,
requirement-result evaluation, charts, chatbot, live-model evaluations, Docker,
or a public demo. The public repository is [JohnZargaryan/aerotest-copilot](https://github.com/JohnZargaryan/aerotest-copilot).
See [GitHub Actions](https://github.com/JohnZargaryan/aerotest-copilot/actions) for hosted check results; local results below are reported separately.

Latest local verification: 27 GoogleTest tests (including 20 shared configuration cases
and 192 state/signal combinations),
80 pytest tests, lint, schema freshness, dependency check, TypeScript and production
build. See [development log](docs/development-log.md) for actual results and limitations.

## Start on Windows

Prerequisites: Git, Python 3.12, and Node.js (tested with 25.0.0 / npm 11.6.2).
No Docker, VS Code, API key, or full Visual Studio installation is required today.

From the repository root in PowerShell:

```powershell
.\scripts\bootstrap-windows.ps1
.\scripts\verify.ps1
```

If Python is not on PATH, provide its executable:

```powershell
.\scripts\bootstrap-windows.ps1 -Python 'C:\path\to\python.exe'
```

Bootstrap downloads the pinned w64devkit toolkit into ignored `.tools/`, checks
its published SHA256 before extraction, creates `.venv/`, and installs locked
Python/npm dependencies. It does not change your system PATH. First CMake setup
downloads checksum-pinned GoogleTest and nlohmann/json archives.
Stop a running frontend preview before rerunning bootstrap: Windows can lock
native npm dependencies while the preview is using them.

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn aerotest.app:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open [API documentation](http://127.0.0.1:8000/docs). From another terminal:

```powershell
npm.cmd --prefix frontend run dev
```

Open the local URL printed by Vite. If your folder path contains `#`, the launcher
automatically builds and serves a preview instead of Vite hot reload (which cannot
resolve that path correctly). After edits, run `npm.cmd --prefix frontend run build`
in another terminal and refresh the browser. No project relocation is required.
Production preview:

```powershell
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run preview
```

Validate configuration directly (this does **not** run a simulation):

```powershell
'{"scenario_id":"healthy-baseline"}' | .\build\aerotest-sim.exe --validate-config
```

Run the healthy baseline (JSON output, no wall-clock waiting):

```powershell
'{"scenario_id":"healthy-baseline","seed":42,"duration_ms":30000}' | .\build\aerotest-sim.exe --run
```

Use `scenario_id` = `sensor-disagreement` for a repeatable sensor bias and DEGRADED transition.
See [sensor-disagreement behavior](docs/disagreement.md).

Use `scenario_id` = `missing-messages` for delayed/dropped samples and freshness transitions.
See [missing-message behavior](docs/missing-messages.md).

Use `scenario_id` = `battery-degradation` for a deterministic discharge.
See [battery behavior](docs/battery.md). All four declared scenarios now run.
See [baseline behavior and replay format](docs/baseline.md).

## Linux / CI setup

Use Python 3.12, Node.js 25.0.0, a C++20 compiler (GCC 13+), CMake 4.4.3 and Ninja 1.13.2.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install cmake==4.4.3 ninja==1.13.2
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
python -m pytest -q
ruff check backend scripts
python scripts/export_contracts.py --check
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
```

The initial Linux GitHub Actions run passed. Hosted results are available in
[GitHub Actions](https://github.com/JohnZargaryan/aerotest-copilot/actions);
the local verification above was performed on Windows.

## Design and learning

- [Architecture and public interfaces](docs/architecture.md)
- [Requirements catalog](docs/requirements.json)
- [State machine design](docs/state-machine.md)
- [Development roadmap](docs/backlog.md)
- [Interview guide and exercise](docs/interview-guide.md)
- [Dependency provenance](docs/dependencies.md)
- [Portfolio presentation plan](docs/portfolio.md)

Source layout: `simulator/` for C++, `backend/` for Python, `frontend/` for React,
`contracts/` for shared schemas/cases. Runtime data and local test reports are ignored.

## Development

Developed with OpenAI Codex assistance. Implemented features, test results, and
planned capabilities are documented separately.
