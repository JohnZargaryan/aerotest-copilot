# Local Docker setup

Implemented with OpenAI Codex assistance. Docker packages the existing educational
simulation, API and scripted investigation. It adds no live model or external service.

## Run and stop

Install Docker and Compose v2 and start the Linux container engine. On Windows,
Docker Desktop must be running; having the command installed alone is insufficient.
Run these commands from the repository root:

```sh
docker compose up --build --detach --wait
docker compose ps
```

Open http://127.0.0.1:5173/. Only the web port is published, bound to local loopback.
`/api/v1/health` on that same address tests the frontend-to-API proxy. The API is
reachable by the web service inside the Compose network. Native development commands
remain available separately; Docker does not mount or alter your native database.

If port 5173 is occupied, use a different port before starting. PowerShell:

```powershell
$env:AEROTEST_WEB_PORT = '5174'
docker compose up --build --detach --wait
```

POSIX shell:

```sh
AEROTEST_WEB_PORT=5174 docker compose up --build --detach --wait
```

Then open port 5174. Stop containers and the project network with:

```sh
docker compose down
```

SQLite lives in the project-scoped named `runs` volume, mounted at `/app/runtime`.
Ordinary `down`, rebuilds and container replacement retain executions. Keep the same
Compose project name to reuse them. `down --volumes` deletes that project's saved
runs, so do not use it for data you want to retain. Docker's volume is local storage,
not a backup or a synchronised copy of native `runtime/aerotest.sqlite`.

## Build contents

One multi-stage Dockerfile builds two targets. `api-build` compiles C++20 with
Debian trixie's compiler, CMake 4.4.3 and Ninja 1.13.2, then installs the existing
hash-locked Python dependencies in a virtual environment. The `api` target copies
only the executable, environment and application package; it runs as UID 10001.
The existing full Python lock includes test/lint packages; these are retained to
avoid introducing a second dependency resolution. Compiler tools are excluded.

`web-build` uses the existing npm lock, runs frontend tests and builds static assets.
The `web` target serves those files through nginx and preserves `/api/` paths when
proxying. No Vite development server runs in the final container. Both services have
health checks; API health is a liveness check, not proof of successful simulation or
writable storage. The verification below exercises those separately.

Official Python 3.12.14, Node 25.0.0 and nginx 1.30.5 images are pinned by manifest
index SHA256 in the Dockerfile. The Python/Node versions match existing project
baselines. Debian OS packages are resolved during build rather than pinned to a
repository snapshot, so images are not promised to be byte-identical. C++ archives
retain their CMake checksum checks. `.dockerignore` permits only build inputs;
host environments, build outputs, runtime data, secrets and evaluation keys are
excluded. Application runtime has no evaluation dataset.

## Isolated verification

With Python 3.12 and Docker available, run:

```sh
python scripts/verify_docker.py
```

On Windows with the existing native environment:

```powershell
.\.venv\Scripts\python.exe scripts/verify_docker.py
```

The script builds from source under a random test project name and selects an
unused loopback port. It checks the HTML and production assets, proxied API health,
all four simulation scenarios, saved results, scoped reports and grounded scripted
citations. It replaces the containers/network while preserving the test volume,
then retrieves all four original executions. Finally it removes only that random
project's containers/network/volume, including on failure. It does not stop your
normal project or delete its saved executions. A rare port-allocation race fails
visibly; rerun after checking the conflicting process. Set `AEROTEST_DOCKER` to the
Docker executable path if it is absent from PATH.

GitHub Actions runs this same script on a standard Ubuntu runner without publishing
images or deploying the app. The smoke check verifies HTTP behavior and persistence;
it does not replace visual browser inspection or the C++/Python test suites.
