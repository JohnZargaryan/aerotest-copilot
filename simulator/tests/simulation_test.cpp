#include "aerotest/freshness.hpp"
#include "aerotest/simulation.hpp"

#include <stdexcept>
#include <gtest/gtest.h>

using aerotest::Config;
using aerotest::run_simulation;

TEST(Baseline, StartupNominalShutdownAtExactTimes) {
    const auto run = run_simulation(Config{"healthy-baseline"});
    auto transitions = nlohmann::json::array();
    for (const auto& event : run.at("records")) {
        if (event.at("event_code") == "STATE_TRANSITION") {
            transitions.push_back({event.at("sim_time_ms"), event.at("state")});
        }
    }
    EXPECT_EQ(transitions, (nlohmann::json{{0, "STARTUP"}, {1000, "NOMINAL"},
                                         {30000, "SHUTDOWN"}}));
    EXPECT_EQ(run.at("records").size(), 903U);
}

TEST(Baseline, MinimumDurationShutsDownBeforeNominal) {
    const auto run = run_simulation(Config{"healthy-baseline", 42, 1000, 100});
    EXPECT_EQ(run.at("records").size(), 32U);
    EXPECT_EQ(run.at("records").back().at("state"), "SHUTDOWN");
    for (const auto& event : run.at("records")) EXPECT_NE(event.at("state"), "NOMINAL");
}

TEST(Baseline, ReplayIsByteIdenticalWithoutSharedRandomState) {
    const auto first = run_simulation(Config{"healthy-baseline"}).dump();
    const auto other = run_simulation(Config{"healthy-baseline", 43}).dump();
    EXPECT_EQ(first, run_simulation(Config{"healthy-baseline"}).dump());
    EXPECT_NE(first, other);
}

TEST(Baseline, KnownSeedAndExtremeSeedsProduceBoundedReadings) {
    const auto known = run_simulation(Config{"healthy-baseline", 42, 1000, 100});
    EXPECT_EQ(known.at("records").at(1).at("measurement"), 20063);
    EXPECT_EQ(known.at("records").at(2).at("measurement"), 20033);
    for (const auto seed : {0U, 42U, 4294967295U}) {
        const auto run = run_simulation(Config{"healthy-baseline", seed, 120000, 100});
        EXPECT_EQ(run.at("records").size(), 3603U);
        for (const auto& event : run.at("records")) {
            if (event.at("event_code") == "SENSOR_SAMPLE") {
                EXPECT_GE(event.at("measurement").get<int>(), 19900);
                EXPECT_LE(event.at("measurement").get<int>(), 20100);
            }
        }
    }
}

TEST(Baseline, RecordIdsAndSequenceAreConsistent) {
    const auto run = run_simulation(Config{"healthy-baseline"});
    int previous_time = -1;
    unsigned sequence = 0;
    for (const auto& event : run.at("records")) {
        EXPECT_EQ(event.at("sequence"), sequence);
        EXPECT_EQ(event.at("run_id"), run.at("run_id"));
        EXPECT_EQ(event.at("event_id"), run.at("run_id").get<std::string>() +
                                         "-e" + std::to_string(sequence++));
        const int time = event.at("sim_time_ms");
        EXPECT_GE(time, previous_time);
        EXPECT_EQ(time % 100, 0);
        previous_time = time;
    }
}

TEST(Baseline, RawStructCannotBypassConfigValidation) {
    EXPECT_THROW(run_simulation(Config{"healthy-baseline", 42, 1050, 100}), std::invalid_argument);
    EXPECT_THROW(run_simulation(Config{"healthy-baseline", 42, 1000, 0}), std::invalid_argument);
}

TEST(Baseline, UnimplementedScenariosAreRejected) {
    EXPECT_THROW(run_simulation(Config{"battery-degradation"}), std::invalid_argument);
}


TEST(DisagreementScenario, DegradesAt2500AndLatchesAfterRecovery) {
    const auto run = run_simulation(Config{"sensor-disagreement", 42, 5000, 100});
    auto transitions = nlohmann::json::array();
    for (const auto& event : run.at("records")) {
        if (event.at("event_code") == "STATE_TRANSITION")
            transitions.push_back({event.at("sim_time_ms"), event.at("state")});
    }
    EXPECT_EQ(transitions, (nlohmann::json{{0, "STARTUP"}, {1000, "NOMINAL"},
                                         {2500, "DEGRADED"}, {5000, "SHUTDOWN"}}));
}

TEST(DisagreementScenario, ShutdownWinsAtDetectionTick) {
    const auto run = run_simulation(Config{"sensor-disagreement", 42, 2500, 100});
    for (const auto& event : run.at("records")) EXPECT_NE(event.at("state"), "DEGRADED");
    EXPECT_EQ(run.at("records").back().at("state"), "SHUTDOWN");
}


TEST(Freshness, InclusiveAgeBoundaryAndInvalidFuture) {
    EXPECT_TRUE(aerotest::sample_is_fresh(300, 0));
    EXPECT_FALSE(aerotest::sample_is_fresh(301, 0));
    EXPECT_FALSE(aerotest::sample_is_fresh(100, 200));
    EXPECT_TRUE(aerotest::sample_is_fresh(200, 200));
}
