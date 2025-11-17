# URL Shortener API

Scalable FastAPI service for authenticated URL shortening backed by MongoDB, Redis, and Celery. The project is production-ready with JWT authentication, async persistence via Motor, background analytics processing, and containerized infrastructure.

## Features

- FastAPI async API with lifespan-managed connections
- MongoDB for persistence with optimized indexes and TTL expiry
- Redis caching layer for short-code lookups and rate limiting hooks
- Celery workers for asynchronous click analytics and future background jobs
- JWT-based authentication (access and refresh tokens)
- Docker Compose stack for app, MongoDB, Redis, Celery worker/beat, and Flower dashboard
- Structlog-based logging for observability and debugging

## Getting Started

### 1. Configure Environment

Copy the sample environment file and adjust values as needed:

```powershell
Copy-Item .env.example .env
```

Ensure `SECRET_KEY` is a long random string and connection strings point to your MongoDB/Redis instances (or the included Docker services).

### 2. Start Services with Docker

```powershell
docker-compose up --build
```

The API will be available at `http://localhost:8000`. Interactive docs are served at `/docs` and `/redoc`.

### 3. Local Development without Docker

Create and activate a virtual environment, then install dependencies in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .[dev]
uvicorn app.main:app --reload
```

Services expect MongoDB and Redis endpoints. Update `.env` accordingly or run them via Docker containers.

## API Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/health/live` | GET | No | Liveness probe |
| `/api/v1/auth/register` | POST | No | Create a new user |
| `/api/v1/auth/login` | POST | No | Obtain access and refresh tokens |
| `/api/v1/auth/me` | GET | Yes | Retrieve current user profile |
| `/api/v1/auth/refresh` | POST | No | Exchange a refresh token |
| `/api/v1/urls/` | POST | Yes | Create a short URL |
| `/api/v1/urls/` | GET | Yes | List user-owned URLs |
| `/api/v1/urls/{code}` | GET | Yes | URL detail with analytics |
| `/api/v1/urls/{code}` | DELETE | Yes | Remove a short URL |
| `/{code}` | GET | No | Redirect to the target URL |

## Celery Workers

Celery processes run alongside the API to log click analytics. Use the provided services:

- `celery-worker`: executes background tasks
- `celery-beat`: schedules future periodic tasks (available for extension)
- `flower`: monitoring UI at `http://localhost:5555`

## Testing

Run unit tests with:

```powershell
pytest
```

Add `-s` for detailed logging or `--maxfail=1` to stop on first failure.

## Project Structure

```
app/
    api/           # FastAPI routers and dependencies
    core/          # Settings, logging, security helpers
    db/            # MongoDB/Redis setup and indexes
    services/      # Business logic for users and URLs
    schemas/       # Pydantic models
    tasks/         # Celery app and tasks
    utils/         # Shared utilities
```

## Scaling Notes

- Use Cosmos DB for global distribution on Azure while keeping MongoDB-compatible drivers.
- Horizontal scale is achieved via additional API replicas and Celery workers; update `docker-compose.yml` or orchestrator manifests accordingly.
- Integrate Redis Cluster or Azure Cache for Redis for high availability in production.
- Expose structured logs to Azure Monitor or preferred observability stack for diagnostics.
