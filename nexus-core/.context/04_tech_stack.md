# NEXUS Technology Stack

## Overview

NEXUS uses a modern, privacy-first architecture with vendor-agnostic LLM integration.

## Backend

### Framework

- **FastAPI** (Python 3.11+)
- Async-first for real-time voice processing
- WebSocket support for bidirectional audio streaming

### Database

- **Supabase** (PostgreSQL)
  - Primary data store for sessions, reports
  - Row-Level Security (RLS) for multi-tenant isolation
- **pgvector** extension for curriculum embeddings

### ORM & Migrations

- **SQLAlchemy 2.0** with async support
- **Alembic** for database migrations

### Real-Time Voice

- **OpenAI Realtime API** (primary)
- Fallback: Google Gemini, Azure Speech Services
- Audio format: PCM 16-bit, 24kHz

### Vector Store

- **ChromaDB** or **FAISS** for development
- **pgvector** for production (Supabase-native)

## Frontend

### Framework

- **Next.js 14+** (App Router)
- **TypeScript** (strict mode)
- Server Components for initial load performance

### State Management

- **Zustand** for client-side state
- Focus on voice session state (connection, mic, AI speaking)

### UI Components

- **shadcn/ui** (Radix primitives)
- **Tailwind CSS** for styling
- Custom audio visualization components

### Audio Handling

- Web Audio API for visualization
- MediaRecorder API for capture
- WebSocket for streaming

## Infrastructure

### Deployment

- **Vercel** (Frontend)
- **Railway** or **Fly.io** (Backend)
- **Supabase** (Database, Auth, Storage)

### Authentication

- **Supabase Auth** with SSO support
- Role-based access: Student, Teacher, Admin

### Monitoring

- **Sentry** for error tracking
- **Axiom** or **Logflare** for logs (PII-scrubbed only)

## Development Tools

### Package Management

- **Poetry** (Python)
- **pnpm** (Node.js)

### Code Quality

- **Ruff** (Python linting/formatting)
- **ESLint** + **Prettier** (TypeScript)
- **mypy** (Python type checking)

### Testing

- **pytest** + **pytest-asyncio** (Backend)
- **Vitest** + **Testing Library** (Frontend)
- **Playwright** (E2E)

## API Design

### REST Endpoints

- `/api/v1/sessions` - CRUD for oracy sessions
- `/api/v1/reports` - Scout report management
- `/api/v1/curriculum` - Curriculum outcome queries

### WebSocket Endpoints

- `/ws/oracy/{student_code}` - Real-time voice stream

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...

# LLM Providers
OPENAI_API_KEY=sk-...
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview

# Optional fallbacks
GOOGLE_AI_KEY=...
AZURE_SPEECH_KEY=...

# Security
JWT_SECRET=...
ENCRYPTION_KEY=...
```

## Type Sharing Strategy

Use `scripts/sync_types.sh` to generate TypeScript interfaces from Pydantic models:

```bash
# Generates frontend/src/lib/types/api.ts from backend models
./scripts/sync_types.sh
```
