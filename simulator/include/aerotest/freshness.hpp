#pragma once
#include <cstdint>
namespace aerotest {
inline bool sample_is_fresh(int now_ms, int sample_ms) {
    const auto age = std::int64_t{now_ms} - sample_ms;
    return age >= 0 && age <= 300;
}
}  // namespace aerotest
