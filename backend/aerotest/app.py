import asyncio
import sqlite3
from pathlib import Path
from threading import BoundedSemaphore
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response

from aerotest.contracts import HealthResponse, SimulationConfig
from aerotest.runner import RunnerError, run_simulation
from aerotest.storage import RunStore, StoredExecution


def create_app(database_path: Path | None = None) -> FastAPI:
    application = FastAPI(
        title="AeroTest Copilot", version="0.2.0",
        description="Educational simulation with local completed-execution storage.",
    )
    path = database_path or Path(__file__).resolve().parents[2] / "runtime" / "aerotest.sqlite"
    slots = BoundedSemaphore(2)

    @application.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @application.post("/api/v1/config/validate", response_model=SimulationConfig)
    def validate_config(config: SimulationConfig) -> SimulationConfig:
        return config

    @application.post("/api/v1/runs", response_model=StoredExecution, status_code=201)
    def create_run(config: SimulationConfig, response: Response) -> StoredExecution:
        if not slots.acquire(blocking=False):
            raise HTTPException(503, detail={"code": "RUN_CAPACITY"})
        try:
            # Own a subprocess-capable loop in this worker thread, including on Windows.
            result = asyncio.run(run_simulation(config))
            saved = RunStore(path).save(result)
            response.headers["Location"] = f"/api/v1/runs/{saved.execution_id}"
            return saved
        except RunnerError as error:
            status = 504 if error.code == "TIMEOUT" else 502
            if error.code == "START_FAILED":
                status = 503
            raise HTTPException(status, detail={"code": error.code}) from error
        except (sqlite3.Error, OSError, ValueError) as error:
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE"}) from error
        finally:
            slots.release()

    @application.get("/api/v1/runs/{execution_id}", response_model=StoredExecution)
    def get_run(execution_id: UUID) -> StoredExecution:
        try:
            saved = RunStore(path).get(str(execution_id))
        except (sqlite3.Error, OSError, ValueError, RunnerError) as error:
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE"}) from error
        if saved is None:
            raise HTTPException(404, detail={"code": "RUN_NOT_FOUND"})
        return saved

    return application


app = create_app()
