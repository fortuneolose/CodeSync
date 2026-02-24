# CodeSync

> Real-time collaborative code editor with AI assistance — built for portfolio depth.

[![CI](https://github.com/YOUR_USERNAME/codesync/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/codesync/actions)

## What it does

- Multiple users edit the same file simultaneously with zero conflicts (CRDT via Yjs)
- Live cursor presence — see exactly where collaborators are typing
- Monaco Editor (the engine behind VS Code) in the browser
- AI assistant panel: explain selected code, refactor, or chat with context
- Named snapshots and diff-based history
- Full auth with JWT + refresh token rotation

## Architecture

```
Browser (React + Monaco + Yjs)
        │ HTTP REST + WebSocket
        ▼
   FastAPI (Python 3.12)
   ├── REST: /api/auth, /api/sessions, /api/snapshots
   └── WS:  /ws/{session_id}  ← real-time ops broadcast
        │
   Redis pub/sub  ←→  Yjs CRDT engine
        │
   PostgreSQL (users, sessions, snapshots, history)
```

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 18, TypeScript, Vite, Monaco Editor, Yjs |
| State | Zustand |
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Real-time | WebSockets, Redis pub/sub, Yjs CRDT |
| Auth | JWT (access + refresh token rotation) |
| AI | OpenAI API (pluggable) |
| Database | PostgreSQL 16 |
| Testing | pytest + pytest-asyncio, Vitest, Playwright |
| CI/CD | GitHub Actions |
| Deploy | Docker Compose → Fly.io |

## Quick start (Docker)

```bash
git clone https://github.com/YOUR_USERNAME/codesync
cd codesync

cp backend/.env.example backend/.env
# edit backend/.env — set SECRET_KEY and OPENAI_API_KEY

docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## Local development (no Docker)

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Running tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

## Milestones

- [x] Scaffold: mono-repo, Docker Compose, CI pipeline
- [ ] Auth: register, login, JWT, refresh token rotation
- [ ] Sessions: create/join/list with persistent storage
- [ ] Monaco editor shell with language + theme selection
- [ ] Real-time sync: Yjs CRDT over WebSocket + Redis
- [ ] Presence: cursors, user avatars, online list
- [ ] AI assistant: explain, refactor, chat
- [ ] Snapshot/history: save, diff, restore
- [ ] Full test pyramid: unit → integration → E2E
- [ ] Production deploy on Fly.io
