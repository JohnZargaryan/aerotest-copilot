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
simulation. A scripted HTTP endpoint and adapter selection boundary are available. Chat UI,
live-model implementation and arbitrary tool dispatch remain unimplemented. Evidence interpretation is limited to existing checker scopes;
this is not a causal explanation, certified assessment or independent AI evaluation.


## HTTP interface and adapter boundary

GET /api/v1/runs/{execution_id}/investigation returns the same scripted response
as the local interface. Optional query parameters are requirement_id (one of the
four assessed requirements) and mode (default scripted). The response schema is
committed at contracts/scripted-investigation.schema.json and exposed in OpenAPI.

The API selects an Investigator through create_investigator. Currently only the
scripted implementation is available. mode=live returns 503 LIVE_MODE_DISABLED
before loading evidence, with no network request or model SDK. Unknown modes or
invalid UUID/requirement arguments return 422. A missing execution returns 404
RUN_NOT_FOUND. Storage access errors return 503 STORAGE_UNAVAILABLE; invalid
investigation evidence or unresolved citations return 500 INVESTIGATION_INVALID.
Internal exception text is excluded from error responses.

The health response now declares investigation_available=true as an implemented
API capability, not a runtime storage readiness probe or live-model availability.
Endpoints remain local development interfaces; no application deployment is implied.
A future live implementation needs a suitable no-cost design, response validation
and evaluation before it can be enabled. The present adapter protocol intentionally
returns the current scripted response contract; that contract will need explicit
extension for a different mode. Adding a boundary does not claim live AI exists.
