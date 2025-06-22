# AI Documentation Generation Makefile
# Provides common development tasks and environment management

.PHONY: help install dev-install test lint format clean docker-build docker-run docker-dev docker-test

# Default target
help:
	@echo "AI Documentation Generation - Development Commands"
	@echo ""
	@echo "Environment Setup:"
	@echo "  install        Install production dependencies with uv"
	@echo "  dev-install    Install development dependencies with uv"
	@echo "  setup-env      Copy env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  test           Run tests with pytest"
	@echo "  test-cov       Run tests with coverage"
	@echo "  lint           Run ruff linter"
	@echo "  format         Format code with ruff"
	@echo "  type-check     Run mypy type checking"
	@echo "  example        Run basic usage example"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run production container"
	@echo "  docker-dev     Run development container"
	@echo "  docker-test    Run tests in container"
	@echo "  docker-compose Run full development stack"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Clean build artifacts and cache"
	@echo "  docker-clean   Clean Docker images and containers"

# Environment setup
install:
	@echo "Installing production dependencies..."
	uv sync

dev-install:
	@echo "Installing development dependencies..."
	uv sync --extra dev

setup-env:
	@echo "Setting up environment file..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please edit .env with your actual values"; \
	else \
		echo ".env file already exists"; \
	fi

# Development tasks
test:
	@echo "Running tests..."
	uv run pytest src/tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest src/tests/ -v --cov=src/ai_doc_gen --cov-report=html --cov-report=term

lint:
	@echo "Running linter..."
	uv run ruff check src/

format:
	@echo "Formatting code..."
	uv run ruff format src/

type-check:
	@echo "Running type checker..."
	uv run mypy src/

example:
	@echo "Running basic usage example..."
	uv run python examples/basic_usage.py

# Docker tasks
docker-build:
	@echo "Building Docker image..."
	podman build -t ai-doc-gen .

docker-run:
	@echo "Running production container..."
	podman run -it --rm \
		-e OPENAI_API_KEY=$${OPENAI_API_KEY} \
		-e ANTHROPIC_API_KEY=$${ANTHROPIC_API_KEY} \
		-v $(PWD)/data:/app/data \
		ai-doc-gen

docker-dev:
	@echo "Running development container..."
	podman run -it --rm \
		-e OPENAI_API_KEY=$${OPENAI_API_KEY} \
		-e ANTHROPIC_API_KEY=$${ANTHROPIC_API_KEY} \
		-v $(PWD)/src:/app/src:ro \
		-v $(PWD)/examples:/app/examples:ro \
		-v $(PWD)/tests:/app/tests:ro \
		-v $(PWD)/output:/app/output \
		-v $(PWD)/data:/app/data \
		-p 8000:8000 \
		ai-doc-gen:latest

docker-test:
	@echo "Running tests in container..."
	podman run -it --rm \
		-v $(PWD)/src:/app/src:ro \
		-v $(PWD)/tests:/app/tests:ro \
		ai-doc-gen:latest \
		uv run pytest src/tests/ -v

docker-compose:
	@echo "Starting development stack with docker-compose..."
	podman-compose up --build

# Cleanup tasks
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-clean:
	@echo "Cleaning Docker artifacts..."
	podman system prune -f
	podman image prune -f
	podman container prune -f

# Development workflow
dev-setup: setup-env dev-install
	@echo "Development environment setup complete!"

dev-workflow: lint format test
	@echo "Development workflow complete!"

# Quick start
quick-start: dev-setup example
	@echo "Quick start complete! Check the output above for results." 