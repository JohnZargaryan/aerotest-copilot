#include "aerotest/config.hpp"

#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
    try {
        if (argc != 2 || std::string(argv[1]) != "--validate-config") {
            throw std::invalid_argument("foundation supports only --validate-config");
        }
        constexpr std::size_t max_input_bytes = 65536;
        std::string input;
        char character;
        while (std::cin.get(character)) {
            if (input.size() == max_input_bytes) {
                throw std::invalid_argument("configuration exceeds 65536 bytes");
            }
            input.push_back(character);
        }
        const auto config = aerotest::parse_config(nlohmann::json::parse(input));
        std::cout << nlohmann::json{{"schema_version", "1.0"}, {"status", "validated"},
                                   {"config", aerotest::to_json(config)}}.dump() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cout << nlohmann::json{{"schema_version", "1.0"}, {"status", "error"},
                                   {"error", {{"code", "INVALID_CONFIG"},
                                              {"message", error.what()}}}}.dump() << '\n';
        return 2;
    }
}
