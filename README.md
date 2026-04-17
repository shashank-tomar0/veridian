# Veridian — Misinformation Response Engine

AI-native, multimodal misinformation detection and counter-narrative platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VERIDIAN PLATFORM                            │
├──────────┬──────────┬──────────┬──────────┬────────────┬───────────┤
│ Dashboard│ Extension│  Bot     │  API     │  Workers   │  ML       │
│ Next.js  │ Plasmo   │ WA+TG   │ FastAPI  │  Celery    │  PyTorch  │
│ :3000    │ Chrome   │ Webhooks │  :8000   │  Redis     │  HF Hub   │
├──────────┴──────────┴──────────┼──────────┼────────────┼───────────┤
│                                │ Postgres │  Qdrant    │  Neo4j    │
│          Data Layer            │  :5432   │  :6333     │  :7687    │
│                                │ MinIO    │  Redis     │           │
│                                │  :9000   │  :6379     │           │
└────────────────────────────────┴──────────┴────────────┴───────────┘
```

## Quick Start

### 1. Clone & configure

```bash
git clone <repo-url> veridian && cd veridian
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start infrastructure (Docker)

```bash
cd infra && docker compose up -d
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Celery workers

```bash
celery -A workers.celery_app:celery_app worker --loglevel=info
```

### 6. Start the dashboard

```bash
cd dashboard && npm install && npm run dev
```

## Project Structure

```
veridian/
├── backend/           # FastAPI application
│   ├── auth/          # JWT authentication
│   ├── db/            # Database clients (Postgres, Redis, Qdrant, Neo4j)
│   ├── middleware/     # Request-ID, logging middleware
│   ├── models/        # SQLAlchemy ORM models
│   ├── routers/       # API route handlers
│   ├── schemas/       # Pydantic v2 request/response models
│   ├── alembic/       # Database migrations
│   ├── config.py      # pydantic-settings configuration
│   ├── deps.py        # Dependency injection
│   └── main.py        # FastAPI entrypoint
├── ml/                # ML model inference modules
│   ├── text/          # Binoculars, MuRIL
│   ├── image/         # ELA, DIRE, CLIP
│   ├── audio/         # RawNet2, Resemblyzer
│   ├── video/         # FaceForensics++, Temporal, SyncNet
│   └── base.py        # DetectionResult dataclass
├── workers/           # Celery task definitions
│   ├── tasks/         # Modality-specific analysis tasks
│   ├── verification/  # LangGraph claim verification agent
│   └── celery_app.py  # Celery application config
├── dashboard/         # Next.js journalist dashboard
├── extension/         # Plasmo browser extension
├── bot/               # WhatsApp + Telegram bot handlers
├── infra/             # Docker Compose + Kubernetes manifests
├── scripts/           # Data ingestion & model download scripts
├── tests/             # pytest + Jest test suites
└── docs/              # API spec, ML models, deployment guides
```

## API Endpoints

| Method | Endpoint                | Description                        |
| ------ | ----------------------- | ---------------------------------- |
| POST   | `/v1/analyze`           | Submit media for analysis          |
| GET    | `/v1/analyze/{id}`      | Poll analysis status               |
| GET    | `/v1/claims`            | Paginated claim browser            |
| GET    | `/v1/claims/graph`      | Neo4j claim graph for D3.js        |
| POST   | `/v1/voiceprint/verify` | Speaker identity verification      |
| POST   | `/v1/voiceprint/enroll` | Enroll voiceprint                  |
| POST   | `/v1/image/analyze`     | Standalone image analysis          |
| POST   | `/v1/auth/register`     | Register new user                  |
| POST   | `/v1/auth/login`        | JWT token pair                     |
| POST   | `/v1/auth/refresh`      | Refresh access token               |
| GET    | `/v1/health`            | Liveness probe                     |
| GET    | `/v1/ready`             | Readiness probe                    |
| GET    | `/v1/metrics`           | Operational metrics (admin-only)   |

## ML Models

| Model           | Modality | Source                    | Task                       |
| --------------- | -------- | ------------------------- | -------------------------- |
| Binoculars      | Text     | falcon-7b + 7b-instruct  | AI text detection          |
| MuRIL           | Text     | google/muril-base-cased   | Semantic manipulation      |
| ELA             | Image    | Signal processing         | Image forgery detection    |
| DIRE            | Image    | lsml/DIRE                 | AI image detection         |
| CLIP            | Image    | openai/clip-vit-large     | Out-of-context detection   |
| RawNet2         | Audio    | ASVspoof2019              | Voice spoof detection      |
| Resemblyzer     | Audio    | d-vector embeddings       | Speaker identification     |
| FaceForensics++ | Video    | EfficientNet-B4           | Deepfake detection         |
| Temporal        | Video    | Optical flow analysis     | Edit splice detection      |
| SyncNet         | Video    | Audio-visual sync         | Lip-sync verification      |

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

## License

Proprietary — All rights reserved.
