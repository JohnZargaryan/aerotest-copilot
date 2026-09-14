#include "aerotest/config.hpp"

#include <array>
#include <stdexcept>
#include <string_view>

namespace aerotest {
namespace {
std::int64_t integer(const nlohmann::json& input, const char* key,
                     std::int64_t fallback, std::int64_t low, std::int64_t high) {
    if (!input.contains(key)) return fallback;
    const auto& value = input.at(key);
    if (!value.is_number_integer() || value < low || value > high) {
        throw std::invalid_argument(std::string(key) + " must be an integer within bounds");
    }
    return value.get<std::int64_t>();
}
}  // namespace

Config parse_config(const nlohmann::json& input) {
    if (!input.is_object()) throw std::invalid_argument("configuration must be an object");
    constexpr std::array<std::string_view, 5> fields{
        "schema_version", "scenario_id", "seed", "duration_ms", "step_ms"};
    for (const auto& [key, value] : input.items()) {
        bool known = false;
        for (const auto field : fields) known = known || key == field;
        if (!known) throw std::invalid_argument("unknown configuration field: " + key);
    }
    if (input.contains("schema_version") && input.at("schema_version") != "1.0") {
        throw std::invalid_argument("unsupported schema_version");
    }
    if (!input.contains("scenario_id") || !input.at("scenario_id").is_string()) {
        throw std::invalid_argument("scenario_id is required and must be a string");
    }
    Config config;
    config.scenario_id = input.at("scenario_id").get<std::string>();
    constexpr std::array<std::string_view, 4> scenarios{
        "healthy-baseline", "sensor-disagreement", "missing-messages", "battery-degradation"};
    bool known = false;
    for (const auto scenario : scenarios) known = known || config.scenario_id == scenario;
    if (!known) throw std::invalid_argument("unsupported scenario_id");
    config.seed = static_cast<std::uint32_t>(integer(input, "seed", 42, 0, 4294967295LL));
    config.duration_ms = static_cast<int>(integer(input, "duration_ms", 30000, 1000, 120000));
    config.step_ms = static_cast<int>(integer(input, "step_ms", 100, 100, 100));
    if (config.duration_ms % config.step_ms != 0) {
        throw std::invalid_argument("duration_ms must be a multiple of step_ms");
    }
    return config;
}

nlohmann::json to_json(const Config& config) {
    return {{"schema_version", "1.0"}, {"scenario_id", config.scenario_id},
            {"seed", config.seed}, {"duration_ms", config.duration_ms},
            {"step_ms", config.step_ms}};
}
}  // namespace aerotest
