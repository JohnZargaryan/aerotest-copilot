"""Version 1 public contracts. Integer ticks and units avoid floating-point drift."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ScenarioId = Literal[
    "healthy-baseline", "sensor-disagreement", "missing-messages", "battery-degradation"
]
OperatingState = Literal["OFF", "STARTUP", "NOMINAL", "DEGRADED", "SAFE", "SHUTDOWN"]
NonnegativeInt = Annotated[int, Field(strict=True, ge=0)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SimulationConfig(Contract):
    schema_version: Literal["1.0"] = "1.0"
    scenario_id: ScenarioId
    seed: Annotated[int, Field(strict=True, ge=0, le=4294967295)] = 42
    duration_ms: Annotated[int, Field(strict=True, ge=1000, le=120000)] = 30000
    step_ms: Annotated[int, Field(strict=True, ge=100, le=100)] = 100

    @model_validator(mode="after")
    def duration_is_whole_ticks(self) -> "SimulationConfig":
        if self.duration_ms % self.step_ms:
            raise ValueError("duration_ms must be a multiple of step_ms")
        return self


class EventRecord(Contract):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(min_length=1, max_length=80)
    event_id: str = Field(min_length=1, max_length=100)
    sim_time_ms: NonnegativeInt
    sequence: NonnegativeInt
    component_id: str = Field(min_length=1, max_length=80)
    measurement: Annotated[int, Field(strict=True)] | None
    unit: Literal["mdegC", "basis_points", "ms", "none"]
    state: OperatingState
    severity: Literal["INFO", "WARNING", "ERROR"]
    event_code: str = Field(min_length=1, max_length=80)
    details: dict[str, str | int | bool]


class HealthResponse(Contract):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["ok"] = "ok"
    checkpoint: Literal["foundation"] = "foundation"
    simulation_available: Literal[False] = False
    investigation_available: Literal[False] = False
