# SAMVIT

AI-powered multi-tenant Human Resource Management System

## Overview

Modern, secure, and scalable HRMS with FastAPI backend and React frontend.

**Key Features:**
- 🏢 Multi-tenant HRMS (employees, attendance, leave, payroll)
- 🛡️ Security hardened (rate limiting, token revocation, audit logging)
- 🤖 AI-powered HR assistant
- ⚡ High performance (async backend, optimized frontend)

## Quick Start

```bash
# Backend
cd backend && uv sync
docker run -d -p 6379:6379 redis:7-alpine
uv run alembic upgrade head
uv run fastapi dev app/main.py

# Frontend
cd frontend && pnpm install && pnpm dev
```

**Access:**
- Backend API: http://localhost:8000/api/docs
- Frontend: http://localhost:3010

## Documentation

- **[Backend README](backend/README.md)** - API, security, deployment, architecture
- **[Frontend README](frontend/README.md)** - UI components, routing, state management

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Redis, PostgreSQL/SQLite |
| **Frontend** | React 19, TypeScript, Vite, TanStack Router/Query |
| **Security** | JWT, bcrypt, custom rate limiter, audit logging |
| **AI** | LangGraph, Pydantic AI |

## Architecture

```
samvit/
├── backend/          # FastAPI API server
│   ├── app/
│   │   ├── core/     # Security, database, config
│   │   ├── modules/  # Auth, employees, leave, payroll, attendance
│   │   └── ai/       # AI agents
│   └── alembic/      # Database migrations
├── frontend/         # React SPA
│   └── src/
│       ├── routes/   # File-based routing
│       └── components/
└── docker-compose.yaml
```

## Development

```bash
# Run both with docker-compose
docker-compose up

# Or separately
cd backend && uv run fastapi dev app/main.py
cd frontend && pnpm dev
```

## License

See [LICENSE](LICENSE)
