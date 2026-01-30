# Testing Guide

How to test the diarization benchmark system. All tests run through Docker.

## Quick Start

```bash

#Clone Repository
git clone https://github.com/antsiforova/diarization-benchmark.git
cd diarization-benchmark

# Start system and initialize database
make init

# Run all tests
make test

# Run quick demo
make demo
```

## Test Types

### 1. Smoke Test

Basic sanity check.

```bash

docker compose -f docker/docker-compose.yml exec benchmark-app bash scripts/smoke_test.sh

```

Checks: Python version, required files, mock diarization, RTTM parsing.

Expected: All checks pass with green checkmarks.

### 2. Quick Demo

Test end-to-end pipeline on 4 AMI files.

```bash
make demo
```

Expected: 4 files processed, DER/JER metrics calculated.

### 3. Full Test Suite

Runs all unit and integration tests.

```bash
make test
```

Tests: database models, configuration, metrics, benchmark pipeline, API endpoints.

## Manual Testing

### Dashboard Test

```bash
# 1. Start system and initialize database
make init

# Open http://localhost:3000
```

**Check:**
1. Runs list loads
2. Create new run (select ami/mock, click "Start Run")
3. New run appears with status "completed"
4. Click run ID - details page loads
5. Click "DER Chart" - chart displays correctly

## Test Checklist

Before deployment:

```bash
# 1. Start system and initialize database
make init

# 2. Smoke test
docker compose -f docker/docker-compose.yml exec benchmark-app bash scripts/smoke_test.sh

# 3. Full tests
make test

# 4. Re-initialize database after tests
make setup

# 5. Quick demo
make demo

# 6. Database run
make run

# 7. Dashboard - open http://localhost:3000
# Check: runs visible, can launch new run, charts work

# 8. Logs
make logs
# Check: no ERROR messages
```

If all pass - ready to go!
