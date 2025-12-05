# NEXUS - Digital Para-Educator Assistant

AI-powered oracy practice partner for Alberta K-12 EAL students.

## 🎯 Purpose

NEXUS helps English as an Additional Language (EAL) students practice speaking in a safe, encouraging environment. The system generates "Scout Reports" for teachers, providing insights into student engagement and curriculum-aligned progress.

## 🏗️ Architecture

```
nexus-core/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # REST & WebSocket endpoints
│   │   ├── core/     # Configuration, security, privacy
│   │   ├── db/       # SQLAlchemy models
│   │   └── services/ # Business logic (voice, reports, RAG)
│   └── alembic/      # Database migrations
├── frontend/         # Next.js 14 TypeScript frontend
│   ├── src/
│   │   ├── app/      # App Router pages
│   │   ├── components/
│   │   └── lib/      # Hooks, stores, API client
└── docker-compose.yml
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (for voice processing)

### Development Setup

1. **Clone and configure:**

   ```bash
   cp .env.example .env
   # Edit .env with your OPENAI_API_KEY
   ```

2. **Start all services:**

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

3. **Run database migrations:**

   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. **Access the application:**
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8000>
   - API Docs: <http://localhost:8000/docs>

### Local Development (without Docker)

**Backend:**

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## 🔒 Privacy & Security

NEXUS is designed with privacy-first principles for K-12 educational environments:

- **Audio-only processing** - No video capture or facial recognition
- **PII scrubbing** - Automatic removal of identifying information
- **Anonymous student codes** - No personal names stored
- **FOIP compliant** - Aligned with Alberta's privacy regulations
- **Data minimization** - Only essential data retained

See `.context/privacy-charter.md` for full privacy specifications.

## 🎓 Key Features

### For Students

- **Voice Orb Interface** - Intuitive, encouraging visual feedback
- **Real-time Conversation** - Natural voice interaction with AI
- **Safe Practice Space** - Judgment-free speaking environment

### For Teachers

- **Scout Reports** - AI-generated insights from sessions
- **Curriculum Connections** - Links to Alberta learning outcomes
- **Progress Tracking** - Monitor student engagement over time
- **Copyable Reports** - Easy integration with existing workflows

## 📚 Alberta Curriculum Alignment

NEXUS aligns with Alberta Education learning outcomes:

- English Language Arts
- English as a Second Language (ESL)
- Social Studies (cultural bridge topics)

The RAG system uses embeddings of curriculum outcomes to suggest relevant connections in Scout Reports.

## 🛠️ Technology Stack

**Backend:**

- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (async)
- PostgreSQL with pgvector
- OpenAI Realtime API

**Frontend:**

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Zustand (state management)

**Infrastructure:**

- Docker & Docker Compose
- Redis (caching/sessions)

## 📄 Documentation

- `.context/manifest.json` - Project structure reference
- `.context/glossary.md` - Domain terminology
- `.context/privacy-charter.md` - Privacy requirements
- `.context/curriculum-reference.md` - Alberta curriculum alignment
- `.context/tech-stack.md` - Technology decisions

## 🧪 Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm run test

# E2E tests
npm run test:e2e
```

## 📦 Deployment

See deployment documentation for production setup with:

- Azure Container Apps (recommended)
- Kubernetes
- Docker Swarm

## 📝 License

Proprietary - Educational use only within authorized Alberta school districts.

---

Built with ❤️ for Alberta's EAL students and educators.
