"""Bounded execution of the trusted local simulator; no shell or user commands."""

import asyncio
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from aerotest.contracts import Contract, EventRecord, SimulationConfig


class RunnerError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SimulationResult(Contract):
    schema_version: Literal["1.0"]
    simulator_version: Literal["0.5.0"]
    status: Literal["completed"]
    run_id: str = Field(min_length=1, max_length=80)
    config: SimulationConfig
    records: list[EventRecord] = Field(min_length=1, max_length=4000)


async def _execute(command: list[str], payload: bytes, *, timeout: float = 5.0,
                   stdout_limit: int = 2_000_000, stderr_limit: int = 65536) -> bytes:
    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as error:
        raise RunnerError("START_FAILED") from error

    async def read(stream, limit):
        output = bytearray()
        while chunk := await stream.read(8192):
            if len(output) + len(chunk) > limit:
                raise RunnerError("OUTPUT_LIMIT")
            output.extend(chunk)
        return bytes(output)

    async def send():
        try:
            process.stdin.write(payload)
            await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    tasks = [asyncio.create_task(read(process.stdout, stdout_limit)),
             asyncio.create_task(read(process.stderr, stderr_limit)),
             asyncio.create_task(send()), asyncio.create_task(process.wait())]
    try:
        stdout, stderr, _, returncode = await asyncio.wait_for(
            asyncio.gather(*tasks), timeout=timeout
        )
        if returncode != 0:
            raise RunnerError("PROCESS_FAILED")
        if stderr:
            raise RunnerError("UNEXPECTED_STDERR")
        return stdout
    except TimeoutError as error:
        raise RunnerError("TIMEOUT") from error
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        await process.wait()
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def _decode(raw: bytes, config: SimulationConfig) -> SimulationResult:
    try:
        result = SimulationResult.model_validate(json.loads(raw))
        expected_id = (f"run-v0.5.0-schema1.0-{config.scenario_id}-s{config.seed}"
                       f"-d{config.duration_ms}-t{config.step_ms}")
        if result.config != config or result.run_id != expected_id:
            raise ValueError("result does not match requested configuration")
        previous = -1
        for sequence, record in enumerate(result.records):
            if (record.sequence != sequence or record.run_id != result.run_id
                    or record.event_id != f"{result.run_id}-e{sequence}"
                    or not previous <= record.sim_time_ms <= config.duration_ms
                    or record.sim_time_ms % config.step_ms):
                raise ValueError("invalid evidence ordering or identity")
            previous = record.sim_time_ms
        final = result.records[-1]
        if (final.state != "SHUTDOWN" or final.event_code != "STATE_TRANSITION"
                or final.sim_time_ms != config.duration_ms):
            raise ValueError("incomplete simulation")
        return result
    except (ValueError, ValidationError, UnicodeError, RecursionError) as error:
        raise RunnerError("INVALID_RESULT") from error


async def run_simulation(config: SimulationConfig) -> SimulationResult:
    # Revalidate even instances constructed without validation or subsequently mutated.
    normalized = SimulationConfig.model_validate(config.model_dump())
    root = Path(__file__).resolve().parents[2]
    executable = root / "build" / ("aerotest-sim.exe" if os.name == "nt" else "aerotest-sim")
    raw = await _execute([str(executable), "--run"], normalized.model_dump_json().encode())
    return _decode(raw, normalized)
