#include "aerotest/state_machine.hpp"

#include <array>
#include <stdexcept>
#include <gtest/gtest.h>

using aerotest::next_state;
using aerotest::State;
using aerotest::TransitionSignals;

TEST(StateMachine, OffWaitsForExplicitStart) {
    EXPECT_EQ(next_state(State::OFF, {}), State::OFF);
    EXPECT_EQ(next_state(State::OFF, {.safe_required = true, .shutdown_requested = true}),
              State::OFF);
}

TEST(StateMachine, StartEntersStartupOnly) {
    EXPECT_EQ(next_state(State::OFF, {.start_requested = true, .startup_complete = true,
                                     .safe_required = true, .shutdown_requested = true}),
              State::STARTUP);
}

TEST(StateMachine, StartupCompletionGatesFaultDecisions) {
    EXPECT_EQ(next_state(State::STARTUP, {.degradation_required = true, .safe_required = true}),
              State::STARTUP);
    EXPECT_EQ(next_state(State::STARTUP, {.startup_complete = true}), State::NOMINAL);
    EXPECT_EQ(next_state(State::STARTUP, {.startup_complete = true, .degradation_required = true}),
              State::DEGRADED);
    EXPECT_EQ(next_state(State::STARTUP, {.startup_complete = true, .safe_required = true}),
              State::SAFE);
}

TEST(StateMachine, SafeWinsOverDegradation) {
    for (const auto state : {State::STARTUP, State::NOMINAL, State::DEGRADED}) {
        EXPECT_EQ(next_state(state, {.startup_complete = true, .degradation_required = true,
                                    .safe_required = true}), State::SAFE);
    }
}

TEST(StateMachine, NominalHoldsOrDegrades) {
    EXPECT_EQ(next_state(State::NOMINAL, {}), State::NOMINAL);
    EXPECT_EQ(next_state(State::NOMINAL, {.degradation_required = true}), State::DEGRADED);
}

TEST(StateMachine, DegradedDoesNotRecoverWhenFaultClears) {
    const auto degraded = next_state(State::NOMINAL, {.degradation_required = true});
    EXPECT_EQ(next_state(degraded, {}), State::DEGRADED);
    EXPECT_EQ(next_state(degraded, {.safe_required = true}), State::SAFE);
}

TEST(StateMachine, SafeRemainsLatchedUntilShutdown) {
    const auto safe = next_state(State::NOMINAL, {.safe_required = true});
    EXPECT_EQ(next_state(safe, {}), State::SAFE);
    EXPECT_EQ(next_state(safe, {.start_requested = true, .startup_complete = true}), State::SAFE);
    EXPECT_EQ(next_state(safe, {.shutdown_requested = true}), State::SHUTDOWN);
}

TEST(StateMachine, ShutdownWinsFromEveryActiveState) {
    for (const auto state : {State::STARTUP, State::NOMINAL, State::DEGRADED, State::SAFE}) {
        EXPECT_EQ(next_state(state, {.startup_complete = true, .degradation_required = true,
                                    .safe_required = true, .shutdown_requested = true}),
                  State::SHUTDOWN);
    }
    // The shortest permitted run ends at startup completion: shutdown wins.
    EXPECT_EQ(next_state(State::STARTUP, {.startup_complete = true, .shutdown_requested = true}),
              State::SHUTDOWN);
    EXPECT_EQ(next_state(State::STARTUP, {.shutdown_requested = true}), State::SHUTDOWN);
}

TEST(StateMachine, AllSignalCombinationsRespectAllowedEdges) {
    // Independent adjacency table from the documented state graph, including holds.
    constexpr std::array<State, 6> states{State::OFF, State::STARTUP, State::NOMINAL,
                                        State::DEGRADED, State::SAFE, State::SHUTDOWN};
    constexpr bool allowed[6][6] = {
        {true, true, false, false, false, false},
        {false, true, true, true, true, true},
        {false, false, true, true, true, true},
        {false, false, false, true, true, true},
        {false, false, false, false, true, true},
        {false, false, false, false, false, true},
    };
    for (unsigned from = 0; from < states.size(); ++from) {
        for (unsigned bits = 0; bits < 32; ++bits) {
            SCOPED_TRACE(::testing::Message() << "from=" << from << " bits=" << bits);
            const TransitionSignals signals{bool(bits & 1), bool(bits & 2), bool(bits & 4),
                                            bool(bits & 8), bool(bits & 16)};
            const auto result = next_state(states[from], signals);
            const auto to = static_cast<unsigned>(result);
            ASSERT_LT(to, states.size());
            EXPECT_TRUE(allowed[from][to]);
            EXPECT_EQ(next_state(states[from], signals), result);
        }
    }
}

TEST(StateMachine, UnknownEnumIsRejected) {
    EXPECT_THROW(next_state(static_cast<State>(99), {}), std::invalid_argument);
}
