# Healthy-baseline simulation

Educational signal generation, not a validated physical model. No wall-clock
sleep, external services or credentials are required. All four declared scenarios run. This page describes healthy-baseline.

## Behavior

Version 0.5.0 uses integer 100 ms ticks. At t=0, OFF enters STARTUP. At t=1000,
STARTUP enters NOMINAL unless the requested duration has been reached, in which
case SHUTDOWN wins. No sensor/power samples are emitted at or after shutdown.
Every prior tick emits sensor-a, sensor-b, then battery. A state-transition record
precedes the samples on transition ticks. The default 30000 ms run has 903 records;
minimum 1000 ms has 32; maximum 120000 ms has 3603. Fault states are never entered
in this healthy baseline. Sensor disagreement is described in docs/disagreement.md.

Sensor values are 20000 mdegC (20 C) plus deterministic noise in [-100,100].
One uint32 noise state starts at the configured seed and is local to the run.
For each sensor sample, in sensor-a then sensor-b order:

    state = (1664525 * state + 1013904223) modulo 2^32
    noise = (state modulo 201) - 100

Seed 42 gives first readings 20063 and 20033 mdegC. Integer modulo deliberately
has slight distribution bias; this is a repeatable test signal, not statistical
or physical sensor validation. All seeds, including zero, are supported.
Battery is 10000 - tick_index basis points (10000 = 100%), staying healthy even
at the maximum duration. Each sample_time_ms equals its emission tick: no staleness.

## Canonical output

`--run` reads the same bounded configuration as `--validate-config`. Exit 0 returns
one compact JSON object with schema_version, simulator_version, status=completed,
normalized config, run_id, and records. Records conform to event-record.schema.json.
State events use null measurement, unit none, and from_state/to_state details.
Samples use integer measurements and sample_time_ms details. All severity is INFO.

The run ID includes every normalized input field and version:

    run-v0.5.0-schema1.0-healthy-baseline-s{seed}-d{duration_ms}-t{step_ms}

Event IDs append -e{sequence}, with contiguous zero-based sequence numbers.
This reversible encoding avoids hash collisions for the current bounded input
space without adding a cryptographic library. IDs are evidence identities, not
security tokens. Future unique execution metadata belongs outside this output.
Changing the algorithm requires a simulator-version change and replay-test review.

Canonical JSON uses sorted object keys from nlohmann/json, integers, no indentation,
and one LF terminator, including on Windows. No real timestamps or UUIDs occur.
An integration test pins the SHA256 of the 1000 ms, seed 42 result, so CI can detect
compiler/platform drift as well as accidental format changes. The JSON Schema
alone does not enforce chronological ordering or identity relationships; integration
tests check those properties on actual emitted output.

No requirement PASS results or evaluation answer keys are emitted. Requirement
checks and frontend execution remain planned. Completed-run persistence is implemented
as a local Python store (docs/storage.md).
The bounded backend runner is implemented; see docs/runner.md. API health still reports simulation_available=false
because no API simulation capability is exposed yet.
