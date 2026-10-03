# Scripted investigation assistant

ScriptedInvestigator is a local, deterministic Python interface over saved checks.
It uses no language model, API key, network request or paid service. Responses are
explicitly labeled mode="scripted", with assistant_version and checker_version.
It does not interpret free-form questions or infer fault causes from scenario names.

```python
from aerotest.assistant import InvestigationRequest, ScriptedInvestigator
from aerotest.storage import RunStore

assistant = ScriptedInvestigator(RunStore("runtime/aerotest.sqlite"))
answer = assistant.investigate(InvestigationRequest(
    execution_id="<saved execution UUID>", requirement_id="AT-REQ-001"))
print(answer.model_dump_json(indent=2))
```

Omit requirement_id to include all four implemented scoped checks. Only AT-REQ-001,
002, 003 and 006 are selectable. Unknown fields and unsupported requirements are
rejected; inputs are revalidated even if constructed without Pydantic validation.
Missing executions raise LookupError("EXECUTION_NOT_FOUND").

Findings retain the report's exact status, reason and scope. Summary counts apply
only to the selected checks, never full system compliance. Unassessed requirements
004/005 remain explicit. PASS, FAIL and INCONCLUSIVE are preserved without ranking
or promotion. An inconclusive outcome can mean unexercised or ambiguous evidence;
the returned explanation distinguishes those cases.

Every displayed citation is resolved through execution-scoped EvidenceTools and
contains its original event record. At most 20 citations are returned per finding;
for longer chains, the first 10 and last 10 unique IDs are selected. Total and
omitted evidence counts disclose the partial selection. Consult the full check
report for the complete chain. Unresolved citations abort the response rather than
silently disappearing. tool_activity records build_report and performed citation
lookups. Event details remain structured data and never become instructions.

This interface reads saved evidence without modifying storage or rerunning a
simulation. No HTTP endpoint, chat UI, live-model adapter or arbitrary tool dispatcher
is implemented here. Evidence interpretation is limited to existing checker scopes;
this is not a causal explanation, certified assessment or independent AI evaluation.
