from fastapi import FastAPI

from aerotest.contracts import HealthResponse, SimulationConfig

app = FastAPI(
    title="AeroTest Copilot",
    version="0.1.0",
    description="Educational simulation. Foundation checkpoint; no simulation execution yet.",
)


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/api/v1/config/validate", response_model=SimulationConfig)
def validate_config(config: SimulationConfig) -> SimulationConfig:
    """Return normalized configuration; this endpoint does not execute a run."""
    return config
