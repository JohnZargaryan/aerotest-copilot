#pragma once
#include "aerotest/config.hpp"

namespace aerotest {
inline constexpr auto simulator_version = "0.5.0";
// Validates config and runs supported scenarios; no wall-clock dependencies.
nlohmann::json run_simulation(const Config& config);
}  // namespace aerotest
