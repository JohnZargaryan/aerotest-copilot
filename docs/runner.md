# Bounded Python simulator runner

`aerotest.runner.run_simulation(config)` is an asynchronous local Python interface.
Pass a validated SimulationConfig and await a SimulationResult. It revalidates
configuration, launches the repository's build/aerotest-sim executable with --run,
and closes stdin after sending normalized JSON. No shell, executable path from
request data, external service, API key or new dependency is used.

Execution after process creation is limited to five seconds. Stdout and stderr
are drained concurrently, capped at 2,000,000 and 65,536 bytes respectively. Each
reader uses at most one additional 8192-byte chunk when detecting overflow. A
failure, timeout or cancellation kills and waits for the direct child and settles
reader/writer tasks. Tests verify that failed and cancelled children have exited.
This supports the trusted simulator, which spawns no descendants; it is not an
arbitrary-code sandbox or process-tree supervisor. OS process creation and cleanup
are outside the execution timeout. Use an event loop with subprocess support
(the Windows default Proactor loop is supported).

RunnerError exposes stable codes: START_FAILED, TIMEOUT, OUTPUT_LIMIT,
PROCESS_FAILED, UNEXPECTED_STDERR and INVALID_RESULT. Raw child output is not
included in those messages. Invalid input raises Pydantic ValidationError before
launch. Cancellation remains asyncio.CancelledError after cleanup.

Result validation checks the versioned envelope, normalized request agreement,
record contracts, chronological ticks, contiguous sequences, evidence identities
and the final shutdown event. The internal result model accepts simulator 0.5.0;
a version change requires reviewing this adapter. These are integrity checks,
not independent requirement verdicts or physical validation. The result model
is internal and is not yet an HTTP contract.

Example from Python with backend on its import path:

```python
import asyncio
from aerotest.contracts import SimulationConfig
from aerotest.runner import run_simulation

result = asyncio.run(run_simulation(SimulationConfig(scenario_id="healthy-baseline")))
print(result.run_id, len(result.records))
```

No API run endpoint or frontend execution is added. Completed results can be saved
with the separate local RunStore (docs/storage.md). API health still
reports simulation_available=false. Tests run all four maximum-duration scenarios
and real helper processes for timeout, failure, output caps, stdin EOF and cleanup;
malformed or corrupted results are rejected separately.
