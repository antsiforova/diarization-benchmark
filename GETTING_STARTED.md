# Getting Started

Two ways to run the benchmark system: **with Make** (simpler) or **without Make** (manual commands).

## Prerequisites

- Docker and Docker Compose
- Git
- 2GB RAM, 5GB disk space

## Clone Repository

```bash
git clone https://github.com/antsiforova/diarization-benchmark.git
cd diarization-benchmark
```

## Method 1: Using Make (Recommended)

Simplest way to get started. All commands are automated through Makefile.

### Setup

```bash
# Start everything and initialize database (recommended)
make init
```

Alternative (manual steps):
```bash
# Start services only
make up

# Wait for services to start
sleep 30

# Initialize database
make setup
```

### Access Dashboard

Open in browser: http://localhost:3000

### Run Benchmarks

```bash
# Manual runs
make run                  # AMI dataset
make run-sequestered      # Sequestered data

# Quick test (no database)
make demo
```

### View Logs

```bash
make logs                 # Follow all logs
```

### Stop

```bash
make down                 # Stop services
make clean                # Stop and remove all data
```

### All Available Commands

```bash
make help                 # Show all commands
make init                 # Start services + initialize database (recommended)
make up                   # Start all services only
make setup                # Initialize database (after 'make up')
make down                 # Stop services
make restart              # Restart services
make logs                 # View logs
make run                  # Run AMI benchmark
make run-sequestered      # Run sequestered benchmark
make demo                 # Quick test
make clean                # Complete cleanup
```

---

## Method 2: Without Make (Manual)

### Step 1: Start Services

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# Wait for initialization
sleep 30

# Initialize database
docker compose -f docker/docker-compose.yml exec benchmark-app benchmark setup

# Check status
docker compose -f docker/docker-compose.yml ps
```

You should see three services running:
- `benchmark-postgres` - Database
- `benchmark-app` - Dashboard
- `benchmark-scheduler` - Automated runs

### Step 2: Access Dashboard

Open browser: http://localhost:3000

### Step 3: Run Benchmarks

**Option A: Through Dashboard GUI**
1. Click "+ New Run" button
2. Select dataset (ami or sequestered)
3. Click "Start Run"
4. Results appear in table after completion

**Option B: Manual Command**

```bash
# AMI dataset
docker compose -f docker/docker-compose.yml exec benchmark-app \
  python run_and_save.py --dataset ami --model mock

# Sequestered dataset
docker compose -f docker/docker-compose.yml exec benchmark-app \
  python run_and_save.py --dataset sequestered --model mock
```

### Step 4: View Logs

```bash
# All services
docker compose -f docker/docker-compose.yml logs -f

# Specific service
docker compose -f docker/docker-compose.yml logs -f benchmark-app
docker compose -f docker/docker-compose.yml logs -f benchmark-scheduler
docker compose -f docker/docker-compose.yml logs -f postgres
```

### Step 5: Stop Services

```bash
# Stop (keeps data)
docker compose -f docker/docker-compose.yml down

# Stop and remove data
docker compose -f docker/docker-compose.yml down -v
```

---


## Setting Up Datasets

### AMI Corpus

```bash
# Automated setup (annotations only)
python scripts/setup_ami.py --file-ids EN2002a EN2002b EN2002c EN2002d
```

This clones the AMI-diarization-setup repository and extracts annotations.

**Audio files must be downloaded manually** due to licensing:
1. Visit: https://groups.inf.ed.ac.uk/ami/download/
2. Accept license agreement
3. Download Mix-Headset files: EN2002a-d.Mix-Headset.wav
4. Place in: `data/ami/audio/test/`

### Sequestered Data

Already included in repository:
- Audio: `data/sequestered/recordings/audio/`
- Annotations: `data/sequestered/recordings/annotation/`

See [SEQUESTERED_DATA.md](SEQUESTERED_DATA.md) for methodology.

---

## Adding New Datasets

### Step 1: Add to datasets.yaml

Edit `config/datasets.yaml`:

```yaml
my_dataset:
  display_name: "My Custom Dataset"
  type: "custom"
  audio_dir: "data/my_dataset/audio"
  annotation_dir: "data/my_dataset/annotations"
  benchmark:
    name: "Custom Benchmark"
    description: "My test data"
  metadata:
    source: "recorded_2024"
```

### Step 2: Add to schedule

Edit `config/schedule.yaml`:

```yaml
schedules:
  - dataset: my_dataset
    interval_hours: 168    # Weekly
    enabled: true
    description: "Custom dataset weekly evaluation"
```

### Step 3: Restart Scheduler

```bash
# With Make
make restart

# Without Make
docker compose -f docker/docker-compose.yml restart benchmark-scheduler
```

---

## Next Steps

- **Dashboard**: Explore results at http://localhost:3000
- **Documentation**: Read [DESIGN.md](DESIGN.md) for architecture
- **Testing**: See [TESTING.md](TESTING.md) for test suite
- **Data**: Check [SEQUESTERED_DATA.md](SEQUESTERED_DATA.md) for methodology
