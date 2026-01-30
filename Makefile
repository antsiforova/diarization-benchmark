.PHONY: help up down logs demo run run-sequestered dashboard test clean restart setup init

help:
	@echo "Diarization Benchmark - Docker Commands"
	@echo ""
	@echo "Getting Started:"
	@echo "  make init          - Start services + initialize database (recommended)"
	@echo "  make up            - Start all services only"
	@echo "  make setup         - Initialize database (run after 'make up')"
	@echo ""
	@echo "System Control:"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs from all services"
	@echo "  make clean         - Stop and remove all data"
	@echo ""
	@echo "Manual Runs:"
	@echo "  make run           - Run AMI benchmark manually"
	@echo "  make run-sequestered - Run sequestered benchmark manually"
	@echo "  make demo          - Quick test (4 AMI files, no database)"
	@echo ""
	@echo "After 'make init', access:"
	@echo "  Dashboard: http://localhost:3000"
	@echo "  Database:  localhost:5432"

up:
	@echo "Starting all services..."
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "Services are starting..."
	@echo ""
	@echo "Next steps:"
	@echo "  1. Wait for services to initialize"
	@echo "  2. Run: make setup"
	@echo "  3. Open: http://localhost:3000"
	@echo ""
	@echo "Or use 'make init' to do everything automatically"

setup:
	@echo "Initializing database..."
	docker compose -f docker/docker-compose.yml exec benchmark-app benchmark setup
	@echo ""
	@echo "Database initialized!"
	@echo "  Dashboard: http://localhost:3000"

init:
	@echo "Starting services and initializing database..."
	docker compose -f docker/docker-compose.yml up -d
	@echo "Waiting for services to start..."
	@sleep 30
	@echo "Initializing database..."
	docker compose -f docker/docker-compose.yml exec benchmark-app benchmark setup
	@echo ""
	@echo "System ready!"
	@echo "  Dashboard: http://localhost:3000"

down:
	@echo "Stopping services..."
	docker compose -f docker/docker-compose.yml down

restart:
	@echo "Restarting services..."
	docker compose -f docker/docker-compose.yml restart

logs:
	docker compose -f docker/docker-compose.yml logs -f

dashboard:
	@echo "Dashboard is available at http://localhost:3000"
	@echo "Use 'make up' to start the system"

run:
	@echo "Running AMI benchmark in Docker..."
	docker compose -f docker/docker-compose.yml exec benchmark-app python run_and_save.py --dataset ami --model mock

run-sequestered:
	@echo "Running sequestered benchmark in Docker..."
	docker compose -f docker/docker-compose.yml exec benchmark-app python run_and_save.py --dataset sequestered --model mock

demo:
	@echo "Running quick demo in Docker..."
	docker compose -f docker/docker-compose.yml exec benchmark-app python test_ami_files.py

test:
	@echo "Running test suite in Docker..."
	docker compose -f docker/docker-compose.yml exec benchmark-app pytest tests/

clean:
	@echo "Stopping and removing all containers and data..."
	docker compose -f docker/docker-compose.yml down -v
	@echo "Cleanup complete"
