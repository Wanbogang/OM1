#!/bin/bash
# Health Check Test for SmartFarm System

echo "SmartFarm Health Check Test"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to test service
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo ""
echo "Testing Core Components..."
echo ""

# Test MAVSDK Writer
test_service "MAVSDK Writer" "http://localhost:5002/health"

# Test Perception Agent
test_service "Perception Agent" "http://localhost:5001/health"

echo ""
echo "Testing Required Files..."
echo ""

# Test required files
test_file() {
    local file_name=$1
    local file_path=$2
    
    echo -n "Testing $file_name... "
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}EXISTS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}MISSING${NC}"
        ((FAILED++))
        return 1
    fi
}

test_file "Mock Drone Script" "bridge/mavsdk_adapter/mock_drone_correct.py"
test_file "Writer Server" "bridge/mavsdk_adapter/server_writer.py"
test_file "Reader Server" "bridge/mavsdk_adapter/server_reader.py"
test_file "Perception Agent" "agents/perception_agent/app.py"

echo ""
echo "Test Results Summary"
echo "======================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed! SmartFarm system is healthy.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed. Please check the failed components above.${NC}"
    exit 1
fi
