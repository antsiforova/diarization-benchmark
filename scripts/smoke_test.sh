#!/bin/bash
# Smoke test script for quick system validation

set -e  # Exit on error

echo "=================================="
echo "Benchmark System - Smoke Test"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        return 1
    fi
}

# Test 1: Check Python version
echo "Test 1: Python version"
python3 --version | grep -q "Python 3.1[1-9]" && test_result 0 "Python 3.11+ installed" || test_result 1 "Python 3.11+ required"

# Test 2: Check .env file
echo ""
echo "Test 2: Environment configuration"
if [ -f .env ]; then
    test_result 0 ".env file exists"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: .env file not found"
    echo "  Run: cp .env.example .env"
fi

# Test 3: Check pip
echo ""
echo "Test 3: Pip installation"
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    test_result 0 "pip installed"
else
    test_result 1 "pip not found"
    exit 1
fi

# Test 4: Check directory structure
echo ""
echo "Test 4: Directory structure"
DIRS_EXIST=0
for dir in src tests scripts config docker; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ✗ $dir/ missing"
        DIRS_EXIST=1
    fi
done
test_result $DIRS_EXIST "Required directories exist"

# Test 5: Check key source files
echo ""
echo "Test 5: Core source files"
FILES_EXIST=0
CORE_FILES=(
    "src/benchmark/core/config.py"
    "src/benchmark/core/models.py"
    "src/benchmark/evaluation/mock_diarization.py"
    "src/benchmark/evaluation/metrics.py"
)
for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file missing"
        FILES_EXIST=1
    fi
done
test_result $FILES_EXIST "Core source files exist"

# Test 6: Check Docker files
echo ""
echo "Test 6: Docker configuration"
DOCKER_OK=0
if [ -f "docker/Dockerfile" ]; then
    echo "  ✓ Dockerfile"
else
    echo "  ✗ Dockerfile missing"
    DOCKER_OK=1
fi
if [ -f "docker/docker-compose.yml" ]; then
    echo "  ✓ docker-compose.yml"
else
    echo "  ✗ docker-compose.yml missing"
    DOCKER_OK=1
fi
test_result $DOCKER_OK "Docker files exist"

echo ""
echo "=================================="
echo "Smoke Test Complete"
echo "=================================="
echo ""