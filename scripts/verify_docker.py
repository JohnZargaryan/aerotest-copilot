"""Build isolated local containers, exercise HTTP behavior, and remove only test data."""

import json
import os
import re
import socket
import subprocess
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "healthy-baseline": None,
    "sensor-disagreement": "AT-REQ-001",
    "missing-messages": "AT-REQ-002",
    "battery-degradation": "AT-REQ-003",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    # A fresh namespace avoids existing services/volumes; no host database is mounted.
    project = "aerotest-check-" + uuid4().hex[:12]
    environment = os.environ.copy()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    environment["AEROTEST_WEB_PORT"] = str(port)
    docker = environment.get("AEROTEST_DOCKER", "docker")
    command = [docker, "compose", "--project-name", project, "--file", str(ROOT / "compose.yaml")]

    def compose(*args: str, check: bool = True) -> None:
        subprocess.run(command + list(args), cwd=ROOT, env=environment, check=check, timeout=900)

    base = f"http://127.0.0.1:{port}"

    def fetch(path: str, payload: dict | None = None):
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(base + path, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=20) as response:
            return response.status, response.read()

    def api(path: str, payload: dict | None = None, status: int = 200):
        actual, raw = fetch(path, payload)
        require(actual == status, f"unexpected status {actual}: {path}")
        return json.loads(raw)

    try:
        compose("up", "--build", "--detach", "--wait", "--wait-timeout", "120")
        for page in ("/", "/demo.html"):
            _, html = fetch(page)
            require(b'id="root"' in html and b'AeroTest Copilot' in html, "frontend not served")
            assets = re.findall(r'(?:src|href)="(\.?/assets/[^"]+)"', html.decode())
            require(bool(assets), f"production assets missing: {page}")
            for asset in assets:
                _, content = fetch(urljoin(page, asset))
                require(bool(content) and not content.startswith(b'<!doctype'), "asset not served")
        require(api("/api/v1/health")["status"] == "ok", "API proxy unavailable")
        saved = []
        for scenario, exercised in SCENARIOS.items():
            run = api("/api/v1/runs", {"scenario_id": scenario}, status=201)
            require(run["result"]["status"] == "completed", "simulator not completed")
            require(run["result"]["config"]["scenario_id"] == scenario, "wrong scenario")
            path = "/api/v1/runs/" + run["execution_id"]
            require(api(path) == run, "saved execution changed")
            report = api(path + "/checks")
            checks = {check["requirement_id"]: check for check in report["checks"]}
            require(checks["AT-REQ-006"]["status"] == "PASS", "transition check failed")
            if exercised:
                require(checks[exercised]["status"] == "PASS", "fault response check failed")
            require(report["unassessed_requirements"] == ["AT-REQ-004", "AT-REQ-005"],
                    "unassessed requirements changed")
            investigation = api(path + "/investigation")
            require(investigation["mode"] == "scripted", "unexpected assistant mode")
            require(investigation["execution_id"] == run["execution_id"], "wrong investigation")
            records = {record["event_id"]: record for record in run["result"]["records"]}
            require(len(investigation["findings"]) == 4, "findings missing")
            for finding in investigation["findings"]:
                require(finding["status"] == checks[finding["requirement_id"]]["status"],
                        "investigation verdict changed")
                for citation in finding["citations"]:
                    require(records.get(citation["event_id"]) == citation, "ungrounded citation")
            saved.append((path, run))
        # Replace both containers and network while keeping this test's named volume.
        compose("down")
        compose("up", "--detach", "--wait", "--wait-timeout", "120")
        for path, run in saved:
            require(api(path) == run, "execution lost after container replacement")
        print("Docker verification passed: frontend assets, 4 scenarios, reports, scripted "
              "citations and 4 persisted executions after container replacement.")
    except Exception:
        compose("logs", "--no-color", check=False)
        raise
    finally:
        # This random project owns only disposable verification containers and volume.
        compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
