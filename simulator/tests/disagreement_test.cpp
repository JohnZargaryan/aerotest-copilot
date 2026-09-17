#include "aerotest/disagreement.hpp"
#include <gtest/gtest.h>
#include <limits>

TEST(Disagreement, StrictAmplitudeAndInclusiveDuration) {
    for (int sign : {-1, 1}) {
        aerotest::DisagreementDetector detector;
        EXPECT_FALSE(detector.update(0, 0, sign * 5000, true));
        EXPECT_FALSE(detector.update(500, 0, sign * 5000, true));
        EXPECT_FALSE(detector.update(600, 0, sign * 5001, true));
        EXPECT_FALSE(detector.update(1000, 0, sign * 5001, true));
        EXPECT_TRUE(detector.update(1100, 0, sign * 5001, true));
    }
}

TEST(Disagreement, RecoveryOrStaleSampleResetsTimer) {
    for (bool fresh : {false, true}) {
        aerotest::DisagreementDetector detector;
        EXPECT_FALSE(detector.update(0, 0, 6000, true));
        EXPECT_FALSE(detector.update(400, 0, fresh ? 5000 : 6000, fresh));
        EXPECT_FALSE(detector.update(500, 0, 6000, true));
        EXPECT_FALSE(detector.update(900, 0, 6000, true));
        EXPECT_TRUE(detector.update(1000, 0, 6000, true));
    }
}

TEST(Disagreement, DifferenceDoesNotOverflow) {
    aerotest::DisagreementDetector detector;
    EXPECT_FALSE(detector.update(0, std::numeric_limits<int>::min(),
                                std::numeric_limits<int>::max(), true));
    EXPECT_TRUE(detector.update(500, std::numeric_limits<int>::min(),
                               std::numeric_limits<int>::max(), true));
}
