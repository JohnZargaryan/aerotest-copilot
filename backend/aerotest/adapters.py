"""Assistant selection boundary. Live services are deliberately unavailable."""

from typing import Literal, Protocol

from aerotest.assistant import InvestigationRequest, ScriptedInvestigation, ScriptedInvestigator
from aerotest.storage import RunStore

AssistantMode = Literal["scripted", "live"]


class Investigator(Protocol):
    def investigate(self, request: InvestigationRequest) -> ScriptedInvestigation: ...


class LiveModeDisabled(RuntimeError):
    pass


def create_investigator(store: RunStore, mode: AssistantMode = "scripted") -> Investigator:
    if mode == "live":
        raise LiveModeDisabled("LIVE_MODE_DISABLED")
    if mode != "scripted":
        raise ValueError("UNSUPPORTED_ASSISTANT_MODE")
    return ScriptedInvestigator(store)
