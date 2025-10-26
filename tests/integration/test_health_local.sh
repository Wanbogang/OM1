#!/bin/bash
# Health Check Test for SmartFarm System
# Tests all components and reports system status

echo "🏥 SmartFarm Health Check Test"
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
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to test process
test_process() {
    local process_name=$1
    local command=$2
    
    echo -n "Testing $process_name... "
    
    if pgrep -f "$command" > /dev/null; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠️  NOT RUNNING${NC}"
        echo "  Start with: $command"
        ((FAILED++))
        return 1
    fi
}

echo ""
echo "📋 Testing Core Components..."
echo ""

# Test Mock Drone
test_process "Mock Drone" "mock_drone_correct.py"

# Test MAVSDK Writer
test_service "MAVSDK Writer" "http://localhost:5002/health"

# Test Perception Agent
test_service "Perception Agent" "http://localhost:5001/health"

echo ""
echo "📁 Testing Required Files..."
echo ""

# Test required files
test_file() {
    local file_name=$1
    local file_path=$2
    
    echo -n "Testing $file_name... "
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✅ EXISTS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ MISSING${NC}"
        ((FAILED++))
        return 1
    fi
}

test_file "Mock Drone Script" "bridge/mavsdk_adapter/mock_drone_correct.py"
test_file "Writer Server" "bridge/mavsdk_adapter/server_writer.py"
test_file "Reader Server" "bridge/mavsdk_adapter/server_reader.py"
test_file "Perception Agent" "agents/perception_agent/app.py"

echo ""
echo "🔗 Testing Integration..."
echo ""

# Test integration between components
echo -n "Testing Perception → MAVSDK communication... "
if curl -s -X POST "http://localhost:5001/detect_base64" \
   -H "Content-Type: application/json" \
   -d '{"image": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="}' \
   -o /dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "📊 Test Results Summary"
echo "======================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! SmartFarm system is healthy.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed. Please check the failed components above.${NC}"
    echo ""
    echo "💡 Quick start commands:"
    echo "  Terminal 1: cd bridge/mavsdk_adapter && python mock_drone_correct.py"
    echo "  Terminal 2: cd bridge/mavsdk_adapter && python server_writer.py"
    echo "  Terminal 3: cd bridge/mavsdk_adapter && python server_reader.py"
    echo "  Terminal 4: cd agents/perception_agent && python app.py"
    echo "  Terminal 5: ./tests/integration/test_health_local.sh"
    exit 1
fi
