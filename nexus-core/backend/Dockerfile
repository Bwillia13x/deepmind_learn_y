# NEXUS Backend Dockerfile
# Multi-stage build for optimized production image

# === Build Stage ===
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev)
RUN poetry install --no-dev --no-interaction --no-ansi

# === Production Stage ===
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=nexus:nexus ./app ./app
COPY --chown=nexus:nexus ./alembic ./alembic
COPY --chown=nexus:nexus ./alembic.ini ./alembic.ini

# Switch to non-root user
USER nexus

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
