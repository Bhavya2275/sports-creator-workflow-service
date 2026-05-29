# Creator Workflow Service

A backend service that manages creator onboarding workflows for a sports platform. Creators move through defined states from discovery to onboarding, with AI-powered qualification scoring.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                     FastAPI App                        │
│                                                        │
│  ┌─────────────┐   ┌──────────────────────────────┐   │
│  │  /creators  │   │  /qualify (async background) │   │
│  └──────┬──────┘   └───────────────┬──────────────┘   │
│         │                          │                   │
│  ┌──────▼──────────────────────────▼──────────────┐   │
│  │               Services Layer                   │   │
│  │  CreatorService | WorkflowService | AIService  │   │
│  └──────────────────────┬─────────────────────────┘   │
│                          │                             │
│  ┌───────────────────────▼─────────────────────────┐  │
│  │           Workflow State Machine                │  │
│  │  DISCOVERED→QUALIFIED→OUTREACH_PENDING→         │  │
│  │  CONTACTED→INTERESTED→ONBOARDED/REJECTED        │  │
│  └───────────────────────┬─────────────────────────┘  │
│                          │                             │
│  ┌───────────────────────▼─────────────────────────┐  │
│  │          SQLAlchemy Async ORM (PostgreSQL)      │  │
│  │   creators | workflow_audit | qualification_jobs│  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Framework | FastAPI | Async-first, automatic OpenAPI docs, Pydantic integration |
| ORM | SQLAlchemy async | Type-safe async database access with PostgreSQL |
| AI Provider | OpenAI GPT | Structured JSON output with `response_format` |
| Async Tasks | FastAPI BackgroundTasks | Simple, zero-dependency, sufficient for the scale |
| State Machine | Explicit transition map | Easy to audit, extend, and test |

### Workflow State Transitions

```
DISCOVERED ──► QUALIFIED ──► OUTREACH_PENDING ──► CONTACTED ──► INTERESTED ──► ONBOARDED
     │              │                │                 │              │
     └──────────────┴────────────────┴─────────────────┴──────────────┴──► REJECTED
```

All transitions are validated against `ALLOWED_TRANSITIONS` in `app/workflow/transitions.py`. Terminal states (`ONBOARDED`, `REJECTED`) cannot be exited.

---

## Project Structure

```
creator-workflow-service/
├── app/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Pydantic settings (env vars)
│   ├── database.py               # Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── creator.py            # Creator ORM model
│   │   ├── audit.py              # WorkflowAudit ORM model
│   │   └── qualification_job.py  # QualificationJob ORM model
│   ├── schemas/
│   │   ├── creator.py            # Request/response Pydantic models
│   │   └── qualification.py      # Qualify request/result models
│   ├── api/v1/
│   │   ├── creators.py           # Creator CRUD + state + history routes
│   │   └── qualification.py      # POST /qualify + GET /qualify/{job_id}
│   ├── services/
│   │   ├── creator_service.py    # Creator CRUD business logic
│   │   ├── workflow_service.py   # State transition + audit logic
│   │   └── ai_service.py        # OpenAI GPT integration
│   ├── workflow/
│   │   ├── states.py             # CreatorState enum
│   │   └── transitions.py       # Allowed transitions map + validator
│   ├── tasks/
│   │   └── qualification_task.py # Background task runner
│   └── core/
│       ├── exceptions.py         # Typed HTTP exceptions
│       ├── logging.py            # Structured logging (structlog)
│       └── dependencies.py      # FastAPI DI (DB session)
├── tests/
│   ├── conftest.py               # Test DB, ASGI client fixtures
│   ├── test_creators.py          # Creator API integration tests
│   ├── test_workflow.py          # State machine unit tests
│   └── test_ai_service.py        # AI service tests (mocked)
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Setup Instructions

### Option A — Local (PostgreSQL required)

```bash
# 1. Clone and enter project
git clone <repo-url>
cd creator-workflow-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL and OPENAI_API_KEY

# 5. Run the server
uvicorn app.main:app --reload

# API docs: http://localhost:8000/docs
```

The application creates the required PostgreSQL tables on startup using SQLAlchemy metadata.

### Option B — Docker + PostgreSQL

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY

docker-compose up --build
# API docs: http://localhost:8000/docs
```

### Running Tests

```bash
pytest
# With coverage:
pytest --cov=app --cov-report=term-missing
```

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Creators

| Method | Path | Description |
|---|---|---|
| `POST` | `/creators` | Create a new creator (starts at DISCOVERED) |
| `GET` | `/creators` | List creators (filter by state, platform) |
| `GET` | `/creators/{id}` | Fetch a single creator |
| `PATCH` | `/creators/{id}/state` | Transition creator to a new state |
| `GET` | `/creators/{id}/history` | Full audit trail for the creator |

### Qualification (AI)

| Method | Path | Description |
|---|---|---|
| `POST` | `/qualify` | Submit async AI qualification job → returns `job_id` |
| `GET` | `/qualify/{job_id}` | Poll for qualification result |

### Example: Create a Creator

```bash
curl -X POST http://localhost:8000/api/v1/creators \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rohit Fitness",
    "platform": "instagram",
    "followers": 250000,
    "bio": "Cricket fitness coach helping athletes perform better"
  }'
```

### Example: Transition State

```bash
curl -X PATCH http://localhost:8000/api/v1/creators/{id}/state \
  -H "Content-Type: application/json" \
  -d '{"new_state": "QUALIFIED", "notes": "Strong sports niche", "changed_by": "analyst@company.com"}'
```

### Example: Qualify with AI

```bash
# Step 1 — submit (async, returns immediately)
curl -X POST http://localhost:8000/api/v1/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "creator_bio": "Professional cricket analyst with 8 years experience",
    "platform": "youtube",
    "followers": 500000,
    "recent_posts": ["IPL match analysis", "Fitness routines for cricketers"]
  }'
# → { "job_id": "...", "status": "PENDING" }

# Step 2 — poll for result
curl http://localhost:8000/api/v1/qualify/{job_id}
# → { "status": "COMPLETED", "result": { "score": 88.5, "is_qualified": true, ... } }
```

---

## Assumptions

1. **Authentication** — not implemented; assumed to be handled by an API gateway layer.
2. **Creator uniqueness** — not enforced (same name/platform can be added multiple times); a unique constraint would be added once business rules are clarified.
3. **AI model** — uses `gpt-5.4-mini` by default; configurable via `OPENAI_MODEL` env var.
4. **Async tasks** — FastAPI BackgroundTasks is used (runs in-process). For production scale, swap in Celery + Redis by changing `app/tasks/qualification_task.py`.
5. **Database** — PostgreSQL is required. Set `DATABASE_URL` in `.env` before starting the server.
6. **Score threshold** — a creator is `is_qualified=true` if score ≥ 60 (configurable via `QUALIFICATION_SCORE_THRESHOLD`).
