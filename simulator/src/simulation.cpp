#include "aerotest/simulation.hpp"
#include "aerotest/disagreement.hpp"
#include "aerotest/state_machine.hpp"

#include <cstdint>
#include <stdexcept>
#include <string>

namespace aerotest {
namespace {
const char* state_name(State state) {
    switch (state) {
    case State::OFF: return "OFF";
    case State::STARTUP: return "STARTUP";
    case State::NOMINAL: return "NOMINAL";
    case State::DEGRADED: return "DEGRADED";
    case State::SAFE: return "SAFE";
    case State::SHUTDOWN: return "SHUTDOWN";
    }
    throw std::invalid_argument("unknown operating state");
}

int next_noise(std::uint32_t& state) {
    // Explicit arithmetic gives the same sequence on every supported compiler.
    state = static_cast<std::uint32_t>((std::uint64_t{1664525} * state + 1013904223) &
                                       0xffffffffULL);
    return static_cast<int>(state % 201U) - 100;
}
}  // namespace

nlohmann::json run_simulation(const Config& input) {
    const auto config = parse_config(to_json(input));
    if (config.scenario_id != "healthy-baseline" &&
        config.scenario_id != "sensor-disagreement") {
        throw std::invalid_argument("scenario is not implemented");
    }
    // Reversible identity over every normalized input field and simulator version.
    const auto run_id = std::string("run-v") + simulator_version + "-schema1.0-" +
        config.scenario_id + "-s" + std::to_string(config.seed) +
        "-d" + std::to_string(config.duration_ms) + "-t" + std::to_string(config.step_ms);
    auto records = nlohmann::json::array();
    auto state = State::OFF;
    auto noise_state = config.seed;
    DisagreementDetector disagreement;
    const auto emit = [&](int time, const char* component, nlohmann::json measurement,
                          const char* unit, const char* code, nlohmann::json details) {
        const auto sequence = records.size();
        records.push_back({{"schema_version", "1.0"}, {"run_id", run_id},
            {"event_id", run_id + "-e" + std::to_string(sequence)},
            {"sim_time_ms", time}, {"sequence", sequence}, {"component_id", component},
            {"measurement", measurement}, {"unit", unit}, {"state", state_name(state)},
            {"severity", "INFO"}, {"event_code", code}, {"details", details}});
    };
    for (int time = 0; time <= config.duration_ms; time += config.step_ms) {
        const bool shutdown = time == config.duration_ms;
        const int sensor_a = shutdown ? 0 : 20000 + next_noise(noise_state);
        const int bias = config.scenario_id == "sensor-disagreement" &&
                         time >= 2000 && time < 4000 ? 6000 : 0;
        const int sensor_b = shutdown ? 0 : 20000 + next_noise(noise_state) + bias;
        const bool degraded = !shutdown && disagreement.update(time, sensor_a, sensor_b, true);
        const auto previous = state;
        state = next_state(state, {.start_requested = time == 0,
                                   .startup_complete = time >= 1000,
                                   .degradation_required = degraded,
                                   .shutdown_requested = time == config.duration_ms});
        if (state != previous) {
            emit(time, "subsystem", nullptr, "none", "STATE_TRANSITION",
                 {{"from_state", state_name(previous)}, {"to_state", state_name(state)}});
        }
        if (state == State::SHUTDOWN) break;
        for (const auto* sensor : {"sensor-a", "sensor-b"}) {
            emit(time, sensor, (std::string(sensor) == "sensor-a" ? sensor_a : sensor_b),
                 "mdegC", "SENSOR_SAMPLE",
                 {{"sample_time_ms", time}});
        }
        emit(time, "battery", 10000 - time / config.step_ms, "basis_points", "POWER_SAMPLE",
             {{"sample_time_ms", time}});
    }
    return {{"schema_version", "1.0"}, {"simulator_version", simulator_version},
            {"status", "completed"}, {"run_id", run_id},
            {"config", to_json(config)}, {"records", records}};
}
}  // namespace aerotest
