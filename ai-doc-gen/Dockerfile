# Multi-stage build for AI Documentation Generation
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files (including README.md for build)
COPY pyproject.toml uv.lock README.md launch_ui.py ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen

# Development stage
FROM python:3.11-slim as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY README.md launch_ui.py pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV ENVIRONMENT="development"

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port for web UI
EXPOSE 5476

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command for development
CMD ["uv", "run", "python", "launch_ui.py"]

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY README.md launch_ui.py pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV ENVIRONMENT="production"

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port for web UI
EXPOSE 5476

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command for production
CMD ["uv", "run", "python", "launch_ui.py"] 