# Design Document

Architecture and design decisions for the diarization benchmark system.

## Project Goals

Build a system that:
1. Automatically evaluates diarization models on test datasets
2. Stores results for tracking over time
3. Provides a web interface for viewing and launching runs
4. Schedules periodic evaluations without manual intervention
5. Makes it easy to add new datasets

## High-Level Architecture

```
┌─────────────────┐
│   Dashboard     │  Web interface (Next.js)
│  (Port 3000)    │  View results, launch runs
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
┌────────▼────────┐  ┌──────▼─────────┐
│   Scheduler     │  │   Run Script   │
│ scheduler.py    │  │run_and_save.py │
│ (Periodic)      │  │  (On-demand)   │
└────────┬────────┘  └──────┬─────────┘
         │                  │
         └──────────┬───────┘
                    │
         ┌──────────▼──────────┐
         │ Mock Diarizer       │  Simulates API
         │ Metrics Calculator  │  Computes DER/JER
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │    PostgreSQL       │  Results storage
         └─────────────────────┘
```

## Data Flow

```
1. Audio File (WAV)
          ↓
2. Mock Diarizer → Hypothesis (who spoke when)
          ↓
3. Compare with Ground Truth (RTTM annotations)
          ↓
4. Calculate Metrics (DER, JER, miss rate, etc.)
          ↓
5. Save to PostgreSQL
          ↓
6. Display in Dashboard
```

## Technology Stack

**Backend (Python)**
- Python 3.11 for async/await support
- SQLAlchemy for database ORM
- asyncpg for PostgreSQL connections
- pyannote.metrics for diarization evaluation
- Pydantic for configuration management

**Frontend (TypeScript)**
- Next.js 14 for React framework
- Recharts for interactive visualizations
- Tailwind CSS for styling

**Infrastructure**
- Docker for containerization
- PostgreSQL 15 for data storage
- Docker Compose for orchestration

## Core Components

### 1. Mock Diarizer (`src/benchmark/evaluation/mock_diarization.py`)

**What it does:**
Simulates a diarization API without external dependencies.

**How it works:**
1. Reads WAV file duration
2. Generates synthetic speaker segments:
   - First 45% → Speaker 0
   - Middle 3% → Both speakers (overlap)
   - Last 52% → Speaker 1
3. Returns RTTM format (same as real API would)

**Why mock?**
- Demonstrates complete pipeline without API dependencies
- Real API requires cloud storage for audio files
- Can be swapped for real client by implementing same interface

**Interface:**
```python
async def diarize(audio_path: Path) -> dict:
    """Returns: {'speakers': [...], 'segments': [...]}"""
```

### 2. Metrics Calculator (`src/benchmark/evaluation/metrics.py`)

**What it does:**
Calculates diarization quality metrics.

**Metrics:**
- **DER** (Diarization Error Rate): Industry standard, sum of miss + false alarm + confusion
- **JER** (Jaccard Error Rate): Intersection over union, measures overlap accuracy
- **Miss**: Speech incorrectly labeled as silence
- **False Alarm**: Silence incorrectly labeled as speech
- **Confusion**: Speech attributed to wrong speaker

**Implementation:**
Uses `pyannote.metrics` library for standard calculations with 0.5s collar tolerance.

### 3. Scheduler (`scheduler.py`)

**What it does:**
Runs benchmarks automatically on a schedule.

**Two modes:**
1. **Config-driven** (default): Read `config/schedule.yaml`, run multiple datasets
2. **Simple mode**: Single dataset, specified interval

**Config example:**
```yaml
schedules:
  - dataset: ami
    interval_hours: 168    # Weekly
    enabled: true
  - dataset: sequestered
    interval_hours: 720    # Monthly
    enabled: true
```

**How it works:**
- Creates async task for each enabled schedule
- Each task loops: run benchmark → sleep → repeat
- All tasks run in parallel (concurrent)

### 4. Main Runner (`run_and_save.py`)

**What it does:**
Runs a benchmark and saves results to database.

**Process:**
1. Load dataset config from `config/datasets.yaml`
2. Create Run record in database (status: running)
3. For each audio file:
   - Run mock diarizer
   - Calculate metrics against ground truth
   - Save Result record
4. Update Run status to completed
5. Calculate aggregate statistics

**Config-driven:**
Dataset paths come from YAML, not hardcoded. Easy to add new datasets.

### 5. Dashboard (`dashboard/`)

**Structure:**
```
dashboard/
  app/
    page.tsx           # Main page (runs list)
    runs/[id]/page.tsx # Run details
    api/runs/route.ts  # API endpoint
  components/
    NewRunForm.tsx     # Launch run dialog
    MetricsChart.tsx   # DER/JER charts
  lib/
    db.ts              # Database queries
```

**Features:**
- View all runs (sortable, filterable)
- Launch new runs via form
- View detailed metrics per run
- Interactive DER/JER charts by dataset
- Responsive design

## Database Schema

```sql
benchmarks
  ├─ id, name, description

datasets
  ├─ id, benchmark_id, name, type, meta_data
  
audio_files
  ├─ id, dataset_id, file_path, duration

runs
  ├─ id, dataset_id, model_name, config
  ├─ status, started_at, completed_at

results
  ├─ id, run_id, audio_file_id
  ├─ metric_name, value, details
```

**Relationships:**
- One benchmark has many datasets
- One dataset has many audio files
- One run belongs to one dataset
- One run has many results (one per file per metric)

**Indexes:**
- `runs.dataset_id` - for filtering by dataset
- `runs.created_at` - for sorting by time
- `results.run_id` - for fetching run details

## Configuration Strategy

**Three layers:**

1. **Environment variables** (`.env`)
   - Secrets: DATABASE_URL, API keys
   - Deployment-specific: ports, hostnames

2. **YAML files** (`config/`)
   - Datasets: paths, metadata
   - Schedules: intervals, enabled flags
   - Version controlled

3. **Code defaults**
   - Fallback values
   - Sensible defaults for development

**Benefits:**
- Easy to deploy in different environments
- Config changes don't require code changes
- Secrets separate from version control
