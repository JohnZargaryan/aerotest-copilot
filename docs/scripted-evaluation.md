# Scripted investigation evaluation

Dataset 1.0 and the runner were authored with OpenAI Codex assistance after the
current implementation. Expected verdicts and required witness times live only in
[evaluation/scripted-cases.json](../evaluation/scripted-cases.json); the application
never loads them. Cases use additional seeds and short durations, plus explicit
synthetic defects. They were reviewed during development. This is a regression
suite, not a blind, external or statistically representative holdout.

## Actual results

Windows / Python 3.12.14, recorded at 2026-10-11T22:05:01.170153+00:00.
Simulator 0.5.0, scripted assistant 0.1.0, checker 0.1.0.
Machine-readable results: [scripted-report.json](../evaluation/scripted-report.json).

- 12/12 cases met all evaluated obligations.
- 18/18 independently specified requirement verdicts matched.
- 44/44 returned citation records exactly matched saved execution evidence.
- Every response preserved checker explanation/scope, selection and summary counts,
  unassessed requirements, execution identity and recorded tool activity.
- Repeated investigations returned identical responses and left storage unchanged.

| Case | Evidence source | Observed requirement verdicts | Returned citations |
| --- | --- | --- | ---: |
| baseline-new-seed | Simulator run | 001: INCONCLUSIVE, 002: INCONCLUSIVE, 003: INCONCLUSIVE, 006: PASS | 3 |
| startup-only-max-seed | Simulator run | 001: INCONCLUSIVE, 002: INCONCLUSIVE, 003: INCONCLUSIVE, 006: PASS | 2 |
| disagreement-observed | Simulator run | 001: PASS | 13 |
| disagreement-shutdown-boundary | Simulator run | 001: INCONCLUSIVE | 0 |
| freshness-observed | Simulator run | 002: PASS | 6 |
| freshness-shutdown-boundary | Simulator run | 002: INCONCLUSIVE | 0 |
| battery-observed | Simulator run | 003: PASS | 3 |
| battery-shutdown-boundary | Simulator run | 003: INCONCLUSIVE | 0 |
| disagreement-late-state | Synthetic defect | 001: FAIL | 13 |
| freshness-late-safe | Synthetic defect | 002: FAIL | 3 |
| battery-late-safe | Synthetic defect | 003: FAIL | 1 |
| battery-missing-witness | Synthetic defect | 003: INCONCLUSIVE | 0 |

The maximum-seed baseline and shutdown boundaries test unexercised obligations.
Three copied traces deliberately delay a recorded response and should FAIL.
Deleting the 8000 ms power sample creates insufficient evidence and should remain
INCONCLUSIVE. Mutated evidence is explicitly synthetic and never presented as a
simulator-produced run. Mutations deep-copy the source and retain structural ordering;
deletions renumber records. All executions are saved in a temporary evaluation database.

## Reproduce

Build the simulator and install the locked dependencies, then run from the repo root:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_scripted.py --check
```

Linux: `python scripts/evaluate_scripted.py --check`. This writes actual results to
ignored artifacts/scripted-evaluation.json, exits nonzero for any failed obligation,
and compares deterministic output with the committed snapshot. Only actual run time
and host metadata are excluded from comparison; canonical-JSON dataset SHA256, versions, all case
results and metrics must match. Local verification and free standard GitHub Actions
run this check. To intentionally record a reviewed new dataset/version snapshot:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_scripted.py --output evaluation/scripted-report.json
```

Review failures before replacing a snapshot. Expected answers must not be inferred
from the output merely to make a failing case pass. Seven evaluator tests demonstrate
rejection of internally consistent but wrong verdicts, modified citation contents,
misleading counts, identity/mode/tool errors and hidden omissions, plus fingerprint
portability across whitespace, key order and Windows/Linux line endings.

## What the numbers establish

Verdict agreement measures these 18 specified obligations. Citation grounding measures
record identity and content, not whether a citation proves a causal explanation.
Report fidelity measures deterministic narration consistency; it is separate from
the independent verdict keys. Unexercised obligations count as INCONCLUSIVE, never
PASS. Configuration/replay requirements 004/005 remain unassessed by the assistant.

No live language model, free-form question answering, causal reasoning or model
accuracy was evaluated. Long-chain truncation and unresolved-citation behavior remain
covered by existing unit tests rather than this small dataset. The suite cannot
establish broader system compliance or behavior on unseen physical aircraft data.
