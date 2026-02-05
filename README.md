# Speaker Diarization Benchmark System

A continuous benchmarking system for speaker diarization models. Runs automated tests on AMI Corpus and custom sequestered data, tracks results in PostgreSQL, and provides a web dashboard for monitoring.

## What This Does

- Automatically evaluates diarization quality on test datasets
- Stores results in a database for tracking over time
- Schedules periodic runs (weekly for AMI, monthly for sequestered)
- Provides a web interface to view results and launch new runs
- Uses mock diarization for testing without external API dependencies

## Quick Start

```bash
# Clone repository
git clone https://github.com/antsiforova/diarization-benchmark.git
cd diarization-benchmark

# Start everything (automatic initialization)
make init

# Open dashboard
http://localhost:3000
```

That's it! The system is now running with:
- PostgreSQL database
- Web dashboard on port 3000
- Automatic scheduler for periodic runs

## Features

**Data Management**
- AMI Corpus integration with automated setup
- Sequestered conversation recordings (guaranteed training-data isolation)
- Config-driven dataset management

**Evaluation**
- Diarization Error Rate (DER) - industry standard metric
- Jaccard Error Rate (JER) - intersection over union
- Per-file and aggregate statistics

**Infrastructure**
- Docker containerization for consistent deployment
- PostgreSQL for persistent storage
- Next.js dashboard with interactive charts
- Automated scheduling system

**Testing**
- Mock diarization client for development
- Full test suite (unit + integration)
- Quick smoke tests

## Project Structure

```
diarization-benchmark/
├── src/benchmark/              # Python backend
│   ├── core/                   # Database models, config
│   ├── evaluation/             # Mock client, metrics calculation
│   └── utils/                  # Logging utilities
├── dashboard/                  # Next.js frontend
│   ├── app/                    # Pages and API routes
│   ├── components/             # React components
│   └── lib/                    # Database queries
├── config/
│   ├── datasets.yaml           # Dataset configurations
│   └── schedule.yaml           # Scheduling rules
├── data/
│   ├── ami/                    # AMI Corpus files
│   └── sequestered/            # Custom recordings
├── docker/                     # Docker setup
├── scripts/                    # Utility scripts
├── run_and_save.py            # Main benchmark runner
└── scheduler.py               # Automated scheduling
```

## How It Works

1. **Audio Input**: WAV files from test datasets
2. **Diarization**: Mock client generates speaker labels (simulates real API)
3. **Evaluation**: Compare against ground truth RTTM annotations
4. **Storage**: Save metrics (DER/JER) to PostgreSQL
5. **Visualization**: View results in web dashboard

## Metrics Explained

**DER (Diarization Error Rate)**
- Measures overall diarization quality
- Components: missed speech, false alarms, speaker confusion
- Lower is better (0.0 = perfect)

**JER (Jaccard Error Rate)**
- Measures overlap accuracy between speakers
- Based on intersection over union
- Range: 0.0 (perfect) to 1.0 (worst)

## Datasets

### AMI Corpus
Meeting recordings from academic scenarios. This project uses 4 test files (EN2002a-d) as a standard benchmark.
- **Setup**: `python scripts/setup_ami.py --file-ids EN2002a EN2002b EN2002c EN2002d`
- **License**: Requires manual download after accepting terms

### Sequestered Data
Custom conversation recordings created specifically for evaluation.
- **Isolation**: Never used for training, guaranteed fresh data
- **Method**: Live recordings → auto-annotation → manual verification
- **Details**: See [SEQUESTERED_DATA.md](SEQUESTERED_DATA.md)

## Usage Examples

**View recent results**
```bash
make logs                    # View all service logs
```

**Run benchmarks manually**
```bash
make run                     # AMI dataset
make run-sequestered         # Sequestered data
```

**Quick test without database**
```bash
make demo                    # Runs 4 AMI files, console output
```

**Stop everything**
```bash
make down                    # Stop services
make clean                   # Stop and delete all data
```

## Configuration

**Schedule** (`config/schedule.yaml`)
```yaml
schedules:
  - dataset: ami
    interval_hours: 168      # Weekly
    enabled: true
  - dataset: sequestered
    interval_hours: 720      # Monthly
    enabled: true
```

**Datasets** (`config/datasets.yaml`)
- Defines audio/annotation paths for each dataset
- Add new datasets without code changes

**Environment** (`.env`)
- Database connection
- Storage paths
- Logging levels

## Development

See [GETTING_STARTED.md](GETTING_STARTED.md) for local development setup.

## Architecture

Key design decisions:

**Mock Diarization**: Uses simulated output instead of real API calls. Demonstrates the complete pipeline without external dependencies. Real API integration would require cloud storage for audio files.

**Config-Driven**: Datasets and schedules defined in YAML files. Add new datasets or change timing without modifying code.

**Containerized**: Docker ensures consistent environment across development and production. Everything runs in containers for reproducibility.

**Isolated Test Data**: Sequestered data approach guarantees no contamination from training sets while staying cost-effective.

## Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - Step-by-step setup
- [DESIGN.md](DESIGN.md) - Architecture details
- [SEQUESTERED_DATA.md](SEQUESTERED_DATA.md) - Test data methodology
- [TESTING.md](TESTING.md) - Testing guide

## Tech Stack

- **Backend**: Python 3.11, SQLAlchemy, asyncpg
- **Frontend**: Next.js 14, React, Recharts
- **Database**: PostgreSQL 15
- **Metrics**: pyannote.metrics, pyannote.core
- **Infrastructure**: Docker, Docker Compose

## Design Trade-offs 

**Note.**
I missed this section by mistake when submitting the project — I overlooked this part of the task. I added it later in the last commit dated Feb 5, which is why it appears at the very end of the document.
I want to be transparent about this. If you consider adding this section after submission to be inappropriate, please feel free to ignore this part.

**What I Optimized For:**
- Quick setup - one command and everything works
- Independence - no external API dependencies
- Easy extensibility - new datasets via YAML config, no code changes

**What I Deliberately Simplified:**
- **Mock vs Real API** - Avoided dependencies and API costs
- **Single Database** - Sufficient for benchmark system volumes, no cluster needed
- **No Database Migrations** - Direct schema creation is acceptable for demos. Production would need migration system with versioning and rollbacks
- **Manual AMI Download** - Required due to licensing terms

## Future Improvements

**Short-term:**
- Support for real diarization APIs
- Email notifications on failures
- Export results to CSV/JSON 

**For Production:**
- User authentication
- Automated database backups
- System monitoring
- Cloud storage integration for larger datasets
- Configurable custom metrics
