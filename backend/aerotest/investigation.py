"""Read-only evidence tools with typed, bounded arguments; no arbitrary queries."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from aerotest.contracts import Contract, EventRecord, OperatingState, SimulationConfig
from aerotest.storage import RunStore

Tick = Annotated[int, Field(strict=True, ge=0, le=120000)]
EventId = Annotated[str, Field(strict=True, min_length=1, max_length=100)]


class EventQuery(Contract):
    execution_id: UUID
    start_ms: Tick = 0
    end_ms: Tick = 120000
    component_id: Literal["sensor-a", "sensor-b", "battery", "subsystem"] | None = None
    state: OperatingState | None = None
    event_code: Literal["SENSOR_SAMPLE", "POWER_SAMPLE", "STATE_TRANSITION"] | None = None
    offset: Annotated[int, Field(strict=True, ge=0, le=4000)] = 0
    limit: Annotated[int, Field(strict=True, ge=1, le=100)] = 50

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.start_ms > self.end_ms:
            raise ValueError("start_ms must not exceed end_ms")
        return self


class EventPage(Contract):
    execution_id: UUID
    run_id: str
    total_matches: int
    next_offset: int | None
    events: list[EventRecord]


class CitationQuery(Contract):
    execution_id: UUID
    event_ids: Annotated[list[EventId], Field(min_length=1, max_length=20)]

    @model_validator(mode="after")
    def unique_ids(self):
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValueError("duplicate citations are not supported")
        return self


class ComparisonQuery(Contract):
    left_execution_id: UUID
    right_execution_id: UUID
    offset: Annotated[int, Field(strict=True, ge=0, le=8000)] = 0
    limit: Annotated[int, Field(strict=True, ge=1, le=100)] = 50


class EventDifference(Contract):
    left: EventRecord | None
    right: EventRecord | None
    measurement_delta: int | None


class ComparisonPage(Contract):
    left_execution_id: UUID
    right_execution_id: UUID
    left_config: SimulationConfig
    right_config: SimulationConfig
    total_differences: int
    next_offset: int | None
    differences: list[EventDifference]


class EvidenceTools:
    def __init__(self, store: RunStore):
        self.store = store

    def _execution(self, execution_id):
        execution = self.store.get(str(execution_id))
        if execution is None:
            raise LookupError("EXECUTION_NOT_FOUND")
        return execution

    def query_events(self, query: EventQuery) -> EventPage:
        query = EventQuery.model_validate(query.model_dump())
        execution = self._execution(query.execution_id)
        matches = [record for record in execution.result.records
                   if query.start_ms <= record.sim_time_ms <= query.end_ms
                   and (query.component_id is None or record.component_id == query.component_id)
                   and (query.state is None or record.state == query.state)
                   and (query.event_code is None or record.event_code == query.event_code)]
        stop = query.offset + query.limit
        return EventPage(execution_id=query.execution_id, run_id=execution.result.run_id,
                         total_matches=len(matches),
                         next_offset=stop if stop < len(matches) else None,
                         events=matches[query.offset:stop])

    def resolve_citations(self, query: CitationQuery) -> list[EventRecord]:
        query = CitationQuery.model_validate(query.model_dump())
        execution = self._execution(query.execution_id)
        available = {record.event_id: record for record in execution.result.records}
        if any(event_id not in available for event_id in query.event_ids):
            raise LookupError("CITATION_NOT_FOUND")
        return [available[event_id] for event_id in query.event_ids]


    def compare_runs(self, query: ComparisonQuery) -> ComparisonPage:
        """Compare recorded content by delivery tick/component/code, not sequence."""
        query = ComparisonQuery.model_validate(query.model_dump())
        left = self._execution(query.left_execution_id).result
        right = self._execution(query.right_execution_id).result
        if (left.simulator_version, left.schema_version, left.config.step_ms) != (
                right.simulator_version, right.schema_version, right.config.step_ms):
            raise ValueError("INCOMPATIBLE_RUNS")

        def index(records):
            indexed = {}
            for record in records:
                key = (record.sim_time_ms, record.component_id, record.event_code)
                if key in indexed:
                    raise ValueError("AMBIGUOUS_EVENT_MATCH")
                indexed[key] = record
            return indexed

        def content(record):
            return record.model_dump(exclude={"run_id", "event_id", "sequence"})

        left_events, right_events = index(left.records), index(right.records)
        differences = []
        for key in sorted(left_events.keys() | right_events.keys()):
            before, after = left_events.get(key), right_events.get(key)
            if before is not None and after is not None and content(before) == content(after):
                continue
            delta = None
            if (before is not None and after is not None and before.unit == after.unit
                    and before.measurement is not None and after.measurement is not None):
                delta = after.measurement - before.measurement
            differences.append(EventDifference(left=before, right=after, measurement_delta=delta))
        stop = query.offset + query.limit
        return ComparisonPage(
            left_execution_id=query.left_execution_id, right_execution_id=query.right_execution_id,
            left_config=left.config, right_config=right.config,
            total_differences=len(differences),
            next_offset=stop if stop < len(differences) else None,
            differences=differences[query.offset:stop])
