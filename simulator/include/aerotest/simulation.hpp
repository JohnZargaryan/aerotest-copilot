#pragma once
#include "aerotest/config.hpp"

namespace aerotest {
inline constexpr auto simulator_version = "0.2.0";
// Validates config and runs only the healthy baseline; no wall-clock dependencies.
nlohmann::json run_baseline(const Config& config);
}  // namespace aerotest
