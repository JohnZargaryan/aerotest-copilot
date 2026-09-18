# Sensor disagreement

Simulator 0.3.0 supports `scenario_id: sensor-disagreement` through `--run`.
This educational fault adds 6000 mdegC to sensor-b at ticks 2000 through 3900 ms.
The bias clears at 4000 ms. Both sensors retain their seeded baseline noise and
fresh sample timestamps; battery readings are unchanged. Short runs may end
before the injection or detection occurs.

The detector consumes measurements, not the scenario ID or injection schedule.
Absolute difference strictly greater than 5000 mdegC starts a persistence timer.
After 500 ms continuously above threshold, it requests DEGRADED. Equality does
not count. An in-range or stale sample resets the timer. The detector assumes
calls at every increasing simulation tick; its freshness input is always true
for baseline and disagreement scenarios. The missing-messages scenario uses
actual sample ages; see docs/missing-messages.md.

The guaranteed difference during injection is 5800..6200 mdegC, so detection is
at 2500 ms for every seed if the run continues past that tick. DEGRADED stays
latched after the readings agree again. Shutdown at 2500 ms wins over detection.
Sample generation precedes detection; transition records precede sample records
on the same tick. Evidence is the measured values, timestamps and state events;
no hidden answer key or requirement PASS result is emitted.

Version 0.3.0 changes versioned run/event identities for both scenarios. Baseline
measurements and timing are unchanged; the previous snapshot was compared after
normalizing only the version text before the new snapshot was recorded.

Tests exercise both signs of the threshold, 400 versus 500 ms persistence,
reset on equality/staleness, integer difference overflow, the full bias window,
replay across seed extremes, short runs, recovery latching and shutdown priority.
