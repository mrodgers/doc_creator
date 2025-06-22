# Development Environment Guide

This document explains how to set up and maintain an isolated development environment for the AI Documentation Generation project.

## 🏗️ Environment Isolation Strategy

### 1. **Python Environment Management with `uv`**

We use `uv` for fast, reliable Python package management:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create isolated environment and install dependencies
uv sync

# Install development dependencies
uv sync --extra dev
```

**Benefits:**
- ✅ **Fast**: 10-100x faster than pip
- ✅ **Reliable**: Deterministic dependency resolution
- ✅ **Isolated**: Each project gets its own environment
- ✅ **Locked**: `uv.lock` ensures reproducible builds

### 2. **Containerized Development with Podman**

#### Development Container
```bash
# Build development image
make docker-build

# Run development container with live code mounting
make docker-dev
```

#### Full Development Stack
```bash
# Start complete development environment
make docker-compose
```

**Benefits:**
- ✅ **Isolated**: Complete environment isolation
- ✅ **Reproducible**: Same environment across all developers
- ✅ **Live Development**: Code changes reflect immediately
- ✅ **Dependencies**: All system dependencies included

### 3. **Environment Variables**

#### Local Development
```bash
# Copy example environment file
make setup-env

# Edit .env with your actual values
nano .env
```

#### Container Development
```bash
# Environment variables are passed through docker-compose
export OPENAI_API_KEY="your_key_here"
export ANTHROPIC_API_KEY="your_key_here"
make docker-compose
```

## 🚀 Quick Start

### Option 1: Local Development
```bash
# 1. Clone and setup
git clone <repository>
cd ai-doc-gen

# 2. Setup environment
make dev-setup

# 3. Run example
make example
```

### Option 2: Containerized Development
```bash
# 1. Clone and setup
git clone <repository>
cd ai-doc-gen

# 2. Setup environment variables
make setup-env
# Edit .env with your API keys

# 3. Start development stack
make docker-compose
```

## 🔧 Development Workflow

### Daily Development
```bash
# 1. Start development environment
make docker-dev

# 2. Make code changes (live mounted)

# 3. Run quality checks
make dev-workflow

# 4. Run tests
make test

# 5. Commit changes (pre-commit hooks run automatically)
git add .
git commit -m "Your changes"
```

### Code Quality Checks
```bash
# Lint code
make lint

# Format code
make format

# Type checking
make type-check

# Run all quality checks
make dev-workflow
```

### Testing
```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Run tests in container
make docker-test
```

## 🐳 Container Architecture

### Multi-Stage Docker Build
```dockerfile
# Builder stage: Install dependencies
FROM python:3.11-slim as builder
# ... dependency installation

# Development stage: Full development environment
FROM python:3.11-slim as development
# ... development tools and live mounting

# Production stage: Minimal runtime
FROM python:3.11-slim as production
# ... production-optimized image
```

### Development Stack Services
```yaml
# docker-compose.yml
services:
  ai-doc-gen:      # Main application
  neo4j:           # Graph database (future)
  dev-tools:       # Development utilities
```

## 🔒 Security and Isolation

### 1. **Non-Root Containers**
```dockerfile
# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
```

### 2. **Environment Variable Isolation**
```bash
# Sensitive data in .env (not committed)
OPENAI_API_KEY=your_actual_key
ANTHROPIC_API_KEY=your_actual_key

# Non-sensitive defaults in docker-compose
CONFIDENCE_THRESHOLD=85.0
GAP_THRESHOLD=70.0
```

### 3. **Volume Mounting Security**
```yaml
# Read-only mounts for source code
volumes:
  - ./src:/app/src:ro
  - ./tests:/app/tests:ro

# Read-write mounts for data
volumes:
  - ./output:/app/output
  - ./data:/app/data
```

## 📊 Environment Monitoring

### Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"
```

### Logging
```python
import logging

# Configure logging based on environment
if os.getenv("ENVIRONMENT") == "development":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

## 🧹 Cleanup and Maintenance

### Regular Cleanup
```bash
# Clean Python artifacts
make clean

# Clean Docker artifacts
make docker-clean

# Full cleanup
make clean && make docker-clean
```

### Dependency Updates
```bash
# Update dependencies
uv sync --upgrade

# Update lock file
uv lock --upgrade
```

## 🔄 CI/CD Integration

### Pre-commit Hooks
```yaml
# pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

### GitHub Actions (Future)
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: make test
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Or use containerized development
make docker-dev
```

#### 2. **API Key Issues**
```bash
# Check environment variables
echo $OPENAI_API_KEY

# Verify .env file
cat .env
```

#### 3. **Dependency Conflicts**
```bash
# Clean and reinstall
make clean
uv sync --reinstall
```

#### 4. **Container Issues**
```bash
# Rebuild containers
make docker-clean
make docker-build
```

## 📋 Environment Checklist

### Before Starting Development
- [ ] Python 3.11+ installed
- [ ] `uv` package manager installed
- [ ] Podman/Docker installed
- [ ] API keys configured
- [ ] Environment file set up
- [ ] Dependencies installed

### Before Committing
- [ ] Code linted (`make lint`)
- [ ] Code formatted (`make format`)
- [ ] Tests passing (`make test`)
- [ ] Type checking passed (`make type-check`)
- [ ] Pre-commit hooks installed

### Before Deployment
- [ ] Production container built
- [ ] Health checks passing
- [ ] Environment variables configured
- [ ] Security scan completed
- [ ] Performance tests passed

## 🎯 Best Practices

### 1. **Always Use Isolated Environments**
- Never install packages globally
- Use `uv` for dependency management
- Use containers for development

### 2. **Keep Secrets Secure**
- Never commit API keys
- Use environment variables
- Use `.env` files for local development

### 3. **Maintain Code Quality**
- Run pre-commit hooks
- Use type hints
- Write comprehensive tests

### 4. **Document Changes**
- Update README.md
- Document new environment variables
- Update docker-compose.yml

This development environment setup ensures complete isolation, reproducibility, and security while maintaining developer productivity. 