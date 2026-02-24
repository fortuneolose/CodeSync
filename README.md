# CodeSync

> **Real-time collaborative code editor with AI assistance** — built as a portfolio-quality full-stack project.

[![CI](https://github.com/YOUR_USERNAME/codesync/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/codesync/actions)
[![Deploy](https://github.com/YOUR_USERNAME/codesync/actions/workflows/deploy.yml/badge.svg)](https://github.com/YOUR_USERNAME/codesync/actions)

**Live demo:** https://codesync-frontend.fly.dev *(deploy to activate)*

---

## What it does

| Feature | Detail |
|---|---|
| **Real-time sync** | Multiple users edit the same file simultaneously with zero conflicts via Yjs CRDT |
| **Presence** | Live cursor positions, colour-coded avatars, online indicator |
| **AI assistant** | Explain, refactor, or chat about any code — streamed token-by-token via SSE |
| **Snapshots** | Save named checkpoints, view history, restore for all connected users |
| **Monaco editor** | The VS Code engine in the browser, 13 languages, dark/light theme |
| **Auth** | JWT + refresh token rotation, bcrypt passwords |
| **Public sessions** | Share a link — anyone can join and collaborate |

---

## Architecture

```
Browser (React 18 + Monaco + Yjs)
        │  REST   │  WebSocket
        ▼         ▼
  ┌─────────────────────────┐
  │   FastAPI  (Python 3.12) │
  │  /api/*  ·  /ws/{slug}  │
  └────────┬────────────────┘
           │
     ┌─────┴──────┐
     │            │
  Redis         PostgreSQL
  (Yjs updates  (users, sessions,
   pub/sub)      snapshots, tokens)
```

**Request flow (real-time edit):**
1. Keystroke → Yjs generates a binary delta
2. `y-websocket` sends it over WS to backend
3. Backend stores it in Redis (`RPUSH session:{slug}:updates`)
4. Backend broadcasts it to every other connected client
5. Each peer's Yjs doc applies the delta — **CRDT guarantees no conflicts**

**New client join flow:**
1. Connect WS → backend replays all stored Redis updates as `SYNC_STEP2` messages
2. Client applies them idempotently → arrives at current shared state instantly

---

## Tech stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | React 18, TypeScript, Vite | Fast DX, type-safe |
| Editor | Monaco Editor | VS Code's engine |
| Real-time | Yjs CRDT, y-websocket, y-monaco | Conflict-free sync |
| State | Zustand | Minimal, fast |
| Backend | FastAPI, Python 3.12 | Async-native, auto-docs |
| ORM | SQLAlchemy 2 (async) | Type-safe async queries |
| Database | PostgreSQL 16 | Relational, reliable |
| Cache/PubSub | Redis 7 | Fast fanout, Yjs persistence |
| Auth | JWT + bcrypt | Stateless, secure |
| AI | OpenAI GPT-4o-mini | Cheapest capable model |
| Testing | pytest, pytest-asyncio, Vitest, Playwright | Full pyramid |
| CI/CD | GitHub Actions | Lint → test → deploy |
| Deploy | Fly.io (backend + frontend) | Free tier, fast cold starts |

---

## Quick start (Docker — recommended)

```bash
git clone https://github.com/YOUR_USERNAME/codesync
cd codesync
cp backend/.env.example backend/.env
# Edit SECRET_KEY and optionally OPENAI_API_KEY in backend/.env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # edit as needed
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

> The Vite dev server proxies `/api` → `http://localhost:8000` and `/ws` → `ws://localhost:8000`.

---

## Running tests

### Backend (50 tests)

```bash
cd backend
python -m pytest -v
```

### Frontend unit tests (Vitest)

```bash
cd frontend
npm test
```

### E2E tests (Playwright) — requires full stack

```bash
docker compose up -d          # start all services
cd frontend
npx playwright install --with-deps chromium
npx playwright test
npx playwright show-report    # view results
```

---

## API reference

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account, returns tokens |
| POST | `/api/auth/login` | Login, returns tokens |
| POST | `/api/auth/refresh` | Rotate refresh token |
| POST | `/api/auth/logout` | Revoke refresh token |
| GET  | `/api/auth/me` | Current user |

### Sessions
| Method | Path | Description |
|---|---|---|
| POST | `/api/sessions` | Create session |
| GET  | `/api/sessions` | List own sessions |
| GET  | `/api/sessions/{slug}` | Session + member list |
| PATCH | `/api/sessions/{slug}` | Update title/language/content |
| DELETE | `/api/sessions/{slug}` | Delete (owner only) |
| POST | `/api/sessions/{slug}/join` | Join public session |

### Snapshots
| Method | Path | Description |
|---|---|---|
| POST | `/api/sessions/{slug}/snapshots` | Save snapshot |
| GET  | `/api/sessions/{slug}/snapshots` | List snapshots |
| POST | `/api/sessions/{slug}/snapshots/{id}/restore` | Restore (owner only) |
| DELETE | `/api/sessions/{slug}/snapshots/{id}` | Delete |

### AI (SSE streaming)
| Method | Path | Description |
|---|---|---|
| POST | `/api/ai/explain` | Explain selected code |
| POST | `/api/ai/refactor` | Suggest refactoring |
| POST | `/api/ai/chat` | Chat with code context |

### WebSocket
| Path | Description |
|---|---|
| `WS /ws/{slug}?token=<jwt>` | y-websocket sync + awareness channel |

---

## Deployment (Fly.io)

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/

# Backend
cd backend
fly launch --name codesync-api --no-deploy
fly secrets set SECRET_KEY=<random> DATABASE_URL=<pg-url> REDIS_URL=<redis-url> OPENAI_API_KEY=<key>
fly deploy

# Frontend
cd frontend
fly launch --name codesync-frontend --no-deploy --dockerfile Dockerfile.prod
fly deploy
```

Set `FLY_API_TOKEN` in GitHub repository secrets to enable automatic deploy on push to `main`.

---

## Project structure

```
codesync/
├── backend/
│   ├── app/
│   │   ├── api/routes/      auth, sessions, ai, snapshots, ws
│   │   ├── core/            config (pydantic-settings)
│   │   ├── db/              SQLAlchemy engine + session factory
│   │   ├── models/          User, RefreshToken, Session, SessionMember, Snapshot
│   │   ├── schemas/         Pydantic request/response models
│   │   ├── services/        Business logic (auth, session, AI, snapshots)
│   │   └── ws/              Yjs protocol utils, connection manager, handler
│   └── tests/
│       ├── unit/            security, yjs_utils, user_service, session_service, ai
│       └── integration/     auth routes, session routes, snapshot routes
├── frontend/
│   ├── src/
│   │   ├── components/      Header, EditorPanel, PresencePanel, AiPanel, SnapshotPanel
│   │   ├── hooks/           useCollabEditor (Yjs + WebsocketProvider + y-monaco)
│   │   ├── pages/           Login, Register, Dashboard, Editor
│   │   ├── services/        api (axios+refresh), authApi, sessionApi, aiApi, snapshotApi
│   │   └── store/           authStore, sessionStore (Zustand)
│   └── e2e/                 Playwright: auth.spec, session.spec, page objects
└── .github/workflows/       ci.yml (test), deploy.yml (Fly.io)
```

---

## Milestones completed

- [x] Mono-repo scaffold, Docker Compose, GitHub Actions CI
- [x] Auth: register, login, JWT access + refresh token rotation, bcrypt
- [x] Session management: CRUD, public/private, member roles
- [x] Monaco editor shell: language selector, dark/light theme toggle
- [x] Real-time sync: Yjs CRDT over WebSocket + Redis persistence
- [x] Presence: live cursors, colour-coded avatars, connection indicator
- [x] AI assistant: explain / refactor / chat with SSE token streaming
- [x] Snapshot history: save, list, restore with live broadcast
- [x] Full test pyramid: 50 backend tests + Vitest + Playwright E2E
- [x] Production deployment: Fly.io config, nginx, GitHub Actions deploy workflow
