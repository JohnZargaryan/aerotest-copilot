import asyncio
import json
import sys

import pytest
from pydantic import ValidationError

from aerotest.contracts import SimulationConfig
from aerotest.runner import RunnerError, _decode, _execute, run_simulation


@pytest.mark.parametrize("scenario", ["healthy-baseline", "sensor-disagreement",
                                      "missing-messages", "battery-degradation"])
def test_real_runner_maximum_duration(scenario):
    config = SimulationConfig(scenario_id=scenario, duration_ms=120000)
    result = asyncio.run(run_simulation(config))
    assert result.config == config
    assert result.records[-1].state == "SHUTDOWN"


@pytest.mark.parametrize("source,code", [
    ("import time; time.sleep(30)", "TIMEOUT"),
    ("import sys; sys.exit(2)", "PROCESS_FAILED"),
    ("import sys; sys.stderr.write('failure')", "UNEXPECTED_STDERR"),
    ("import sys; sys.stdout.write('x'*100000)", "OUTPUT_LIMIT"),
    ("import sys; sys.stderr.write('x'*100000)", "OUTPUT_LIMIT"),
])
def test_real_process_failure_cleanup(source, code, monkeypatch):
    spawned = []
    create = asyncio.create_subprocess_exec

    async def capture(*args, **kwargs):
        process = await create(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", capture)
    with pytest.raises(RunnerError, match=code):
        asyncio.run(_execute([sys.executable, "-c", source], b"{}",
                             timeout=1.0, stdout_limit=1000, stderr_limit=1000))
    assert len(spawned) == 1 and spawned[0].returncode is not None


def test_missing_executable(tmp_path):
    with pytest.raises(RunnerError, match="START_FAILED"):
        asyncio.run(_execute([str(tmp_path / "absent")], b"{}"))


def test_exact_output_limit_and_stdin_eof():
    source = "import sys; data=sys.stdin.buffer.read(); sys.stdout.buffer.write(data)"
    assert asyncio.run(_execute([sys.executable, "-c", source], b"1234",
                                stdout_limit=4)) == b"1234"


@pytest.mark.parametrize("raw", [b"", b"not json", b"\xff", b"{}", b"[]"])
def test_invalid_output(raw):
    with pytest.raises(RunnerError, match="INVALID_RESULT"):
        _decode(raw, SimulationConfig(scenario_id="healthy-baseline"))


@pytest.mark.parametrize("mutation", ["config", "sequence", "event_id", "time", "end"])
def test_corrupted_evidence_is_rejected(mutation):
    config = SimulationConfig(scenario_id="healthy-baseline", duration_ms=1000)
    body = asyncio.run(run_simulation(config)).model_dump()
    if mutation == "config":
        body["config"]["seed"] = 43
    elif mutation == "end":
        body["records"].pop()
    else:
        key, value = {"sequence": ("sequence", 99), "event_id": ("event_id", "wrong"),
                      "time": ("sim_time_ms", 1050)}[mutation]
        body["records"][0][key] = value
    with pytest.raises(RunnerError, match="INVALID_RESULT"):
        _decode(json.dumps(body).encode(), config)


def test_invalid_config_revalidated():
    config = SimulationConfig.model_construct(scenario_id="healthy-baseline", duration_ms=1050)
    with pytest.raises(ValidationError):
        asyncio.run(run_simulation(config))


def test_cancellation_reaps_child(monkeypatch):
    spawned = []
    create = asyncio.create_subprocess_exec

    async def capture(*args, **kwargs):
        process = await create(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", capture)

    async def exercise():
        task = asyncio.create_task(_execute(
            [sys.executable, "-c", "import time; time.sleep(30)"], b"{}"))
        async with asyncio.timeout(5):
            while not spawned:
                await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert spawned[0].returncode is not None

    asyncio.run(exercise())
