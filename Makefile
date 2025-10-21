.PHONY: help install test lint format clean docker-up docker-down run-producer run-dashboard

# Default target
help:
	@echo "Collaborate-Stream - Real-Time SaaS Usage Analytics"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run code linters"
	@echo "  make format        - Format code with black"
	@echo "  make docker-up     - Start all Docker services"
	@echo "  make docker-down   - Stop all Docker services"
	@echo "  make run-producer  - Run Kafka event producer"
	@echo "  make run-dashboard - Run Streamlit dashboard"
	@echo "  make clean         - Clean temporary files"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-fast:
	pytest tests/ -v

# Code quality
lint:
	flake8 kafka/ flink/ storage/ hive/ visualization/ tests/ --max-line-length=100
	mypy kafka/ flink/ storage/ --ignore-missing-imports

format:
	black kafka/ flink/ storage/ hive/ visualization/ tests/ --line-length=100

# Docker operations
docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started! Access:"
	@echo "  - Kafka UI: http://localhost:8080"
	@echo "  - Flink Dashboard: http://localhost:8082"
	@echo "  - MinIO Console: http://localhost:9001"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# Application
run-producer:
	python kafka/producer.py

run-flink:
	python flink/main_flink_job.py

run-dashboard:
	streamlit run visualization/dashboard_streamlit.py

# Data generation
generate-data:
	python hive/load_historical_data.py

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf /tmp/collaborate_stream_data/ 2>/dev/null || true

# Development
dev-setup: install docker-up
	@echo "Development environment ready!"

# Full test suite
ci-test: lint test
	@echo "CI tests passed!"

# Deployment helpers
build-all:
	@echo "Building all components..."
	docker-compose build

# Monitoring
logs-kafka:
	docker-compose logs -f kafka

logs-flink:
	docker-compose logs -f flink-jobmanager flink-taskmanager

logs-all:
	docker-compose logs -f

# Quick start
quickstart: dev-setup generate-data
	@echo ""
	@echo "Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run producer:  make run-producer"
	@echo "  2. Run dashboard: make run-dashboard"
	@echo "  3. View metrics:  http://localhost:8501"
	@echo ""
