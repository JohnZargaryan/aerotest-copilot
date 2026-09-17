#pragma once
#include <cstdint>
#include <optional>

namespace aerotest {
// Call once per increasing simulation tick. Stale samples interrupt persistence.
class DisagreementDetector {
public:
    bool update(int time_ms, int sensor_a, int sensor_b, bool both_fresh) {
        const auto difference = std::int64_t{sensor_a} - sensor_b;
        if (!both_fresh || (difference >= -5000 && difference <= 5000)) {
            started_at_.reset();
            return false;
        }
        if (!started_at_) started_at_ = time_ms;
        return time_ms - *started_at_ >= 500;
    }
private:
    std::optional<int> started_at_;
};
}  // namespace aerotest
