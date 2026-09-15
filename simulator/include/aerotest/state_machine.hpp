#pragma once

namespace aerotest {
enum class State { OFF, STARTUP, NOMINAL, DEGRADED, SAFE, SHUTDOWN };

// The future simulator evaluates timers/measurements to produce these signals.
struct TransitionSignals {
    bool start_requested{false};
    bool startup_complete{false};
    bool degradation_required{false};
    bool safe_required{false};
    bool shutdown_requested{false};
};

// Pure decision function: no clock, measurements, I/O, or hidden mutable state.
// Throws std::invalid_argument if current is not a declared State value.
State next_state(State current, const TransitionSignals& signals);
}  // namespace aerotest
