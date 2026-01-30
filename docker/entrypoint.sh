#!/bin/bash
set -e

echo "Starting Diarization Benchmark System"
echo "======================================"

# Docker-compose healthcheck ensures postgres is ready before starting this container
# Just add a small safety buffer
echo "Waiting for database to be fully ready..."
sleep 5

echo "Database is ready!"

# Execute command
case "$1" in
  benchmark)
    echo "Starting benchmark CLI..."
    exec python -m benchmark.cli
    ;;
  scheduler)
    echo "Starting continuous benchmark scheduler..."
    exec python scheduler.py "${@:2}"
    ;;
  shell)
    echo "Starting interactive shell..."
    exec /bin/bash
    ;;
  *)
    echo "Running custom command: $@"
    exec "$@"
    ;;
esac