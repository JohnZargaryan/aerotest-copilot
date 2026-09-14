#include "aerotest/config.hpp"
#include "test_paths.hpp"

#include <fstream>
#include <stdexcept>
#include <gtest/gtest.h>

TEST(ConfigContract, SharedAcceptanceCases) {
    std::ifstream source(std::string(AEROTEST_SOURCE_DIR) + "/contracts/config-cases.json");
    ASSERT_TRUE(source.good());
    const auto cases = nlohmann::json::parse(source);
    for (const auto& item : cases) {
        SCOPED_TRACE(item.at("name").get<std::string>());
        if (item.at("valid").get<bool>()) {
            EXPECT_NO_THROW(aerotest::parse_config(item.at("input")));
        } else {
            EXPECT_THROW(aerotest::parse_config(item.at("input")), std::invalid_argument);
        }
    }
}

TEST(ConfigContract, DefaultsAndRoundTrip) {
    const auto config = aerotest::parse_config({{"scenario_id", "healthy-baseline"}});
    EXPECT_EQ(config.seed, 42U);
    EXPECT_EQ(config.duration_ms, 30000);
    EXPECT_EQ(config.step_ms, 100);
    EXPECT_EQ(aerotest::to_json(aerotest::parse_config(aerotest::to_json(config))),
              aerotest::to_json(config));
}
