#include "aerotest/state_machine.hpp"

#include <stdexcept>

namespace aerotest {
State next_state(State current, const TransitionSignals& signals) {
    switch (current) {
    case State::OFF:
        return signals.start_requested ? State::STARTUP : State::OFF;
    case State::SHUTDOWN:
        return State::SHUTDOWN;
    case State::STARTUP:
    case State::NOMINAL:
    case State::DEGRADED:
    case State::SAFE:
        break;
    default:
        throw std::invalid_argument("unknown operating state");
    }

    if (signals.shutdown_requested) return State::SHUTDOWN;
    if (current == State::SAFE) return State::SAFE;
    if (current == State::STARTUP && !signals.startup_complete) return State::STARTUP;
    if (signals.safe_required) return State::SAFE;
    if (current == State::DEGRADED || signals.degradation_required) return State::DEGRADED;
    return State::NOMINAL;
}
}  // namespace aerotest
