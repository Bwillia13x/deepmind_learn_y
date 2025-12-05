# NEXUS Backend

The FastAPI backend for NEXUS - Digital Para-Educator Assistant.

## Setup

```bash
# Install dependencies
poetry install

# Copy environment file
cp ../.env.example .env

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
app/
├── api/           # API routes and WebSocket handlers
├── core/          # Configuration, security, middleware
├── db/            # Database models and migrations
├── evals/         # LLM evaluation scripts
└── services/      # Business logic (voice, curriculum, reports)
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_privacy.py
```
