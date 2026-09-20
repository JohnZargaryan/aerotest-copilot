#pragma once
namespace aerotest {
struct BatteryStatus { bool degraded; bool safe; };
inline BatteryStatus battery_status(int basis_points) {
    return {basis_points < 2000, basis_points < 1000};
}
}  // namespace aerotest
