#pragma once

#include <cstdint>
#include <string>
#include <nlohmann/json.hpp>

namespace aerotest {
struct Config {
    std::string scenario_id;
    std::uint32_t seed{42};
    int duration_ms{30000};
    int step_ms{100};
};

// Throws std::invalid_argument for an invalid public input.
Config parse_config(const nlohmann::json& input);
nlohmann::json to_json(const Config& config);
}  // namespace aerotest
