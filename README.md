# m3wory.site

A small temporary file-sharing service: upload a file, choose how long it lives and how many
times it can be downloaded, and get a short link (or QR code) to share.

**Live:** https://m3wory.site

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![CI](https://img.shields.io/github/actions/workflow/status/m3wory/m3wory.site/deploy.yml?branch=main&label=CI%2FCD)

## Features

- Drag-and-drop upload, up to 100 MB per file (configurable).
- Expiry: 1 hour, 6 hours, 24 hours, 3 days, 7 days, 30 days or never.
- Download limit: 1, 3, 10, 50, 100 or unlimited.
- Short link (`/d/<code>`) and a downloadable QR code.
- Expired or fully downloaded files are removed from disk and database by a scheduled cleanup.

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async, asyncpg), Pydantic, pydantic-settings, aiofiles |
| Database | PostgreSQL 16 |
| Frontend | Plain HTML/CSS/JavaScript served by Nginx |
| Infrastructure | Docker Compose, Nginx (reverse proxy, TLS termination), Let's Encrypt (Certbot), cron |
| Quality | pytest, pytest-asyncio, httpx, coverage, ruff |
| CI/CD | GitHub Actions: lint + tests, then deploy to a VPS over SSH |

## Architecture

```text
Browser ──HTTPS──> Nginx ──/api/──> FastAPI ──> PostgreSQL
                     │                  └──────> disk (uploaded files)
                     └── static files
```

The backend is split into layers, each with one responsibility:

```text
api/routes  ->  services/FileService  ->  repositories/FileRepository  (database)
(HTTP only)     (business rules)      ->  services/LocalFileStorage    (disk)
```

- `api/` - thin routes, dependency injection, one place that maps domain errors to HTTP status codes.
- `services/file_service.py` - upload, expiry and download-limit rules; knows nothing about HTTP.
- `repositories/` - all SQL lives here.
- `core/` - settings (`pydantic-settings`) and domain exceptions.
- `main.py` - `create_app()` application factory, so tests can build an app with their own settings.

### Design notes

- **Download limit is exact.** The counter is incremented with a single conditional `UPDATE`
  (`... WHERE download_count < max_downloads`), so parallel requests cannot exceed the limit.
- **Uploads are streamed** to disk in 1 MB chunks and rejected as soon as they exceed the limit
  (HTTP 413) instead of being read into memory.
- **Safe storage.** Files are stored under random names; the original name is sanitized and kept
  only in the database.
- **Short codes** come from `secrets`; collisions are handled by the unique constraint with a retry.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Multipart form: `file`, `expires_hours` (default 24, `0` = never), `max_downloads` (default `0` = unlimited). Returns the short code and metadata. |
| `GET` | `/api/info/{code}` | File metadata, without counting as a download. |
| `GET` | `/api/download/{code}` | Download the file. |

Errors: `404` unknown code, `410` expired or download limit reached, `413` file too large.

```bash
curl -F "file=@report.pdf" -F expires_hours=24 -F max_downloads=3 https://m3wory.site/api/upload
```

Interactive docs (Swagger UI) are available at `http://localhost:8000/docs` in the dev setup.

## Run locally

Requirements: Docker with Compose, and `make` (optional).

```bash
cp .env.example .env        # adjust the passwords
make dev                    # or: docker compose -f docker-compose.dev.yml up -d --build
```

Open http://localhost. The dev setup mounts `backend/` into the container and reloads on changes.

## Tests

```bash
make test        # 24 tests, run in a throwaway container
make test-cov    # with coverage (about 95%, branches included)
make lint        # ruff
```

The tests exercise the real HTTP API against a temporary SQLite database and a temporary upload
directory, so they need no running services. Without Docker:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Deployment

- `docker-compose.yml` is the production setup: only Nginx (80/443) is exposed; backend and
  database stay on the internal Docker network.
- `init-letsencrypt.sh` requests the first certificate; the `certbot` container renews it.
- `make cron-setup` installs the hourly cleanup job.
- Every merge to `main` runs lint and tests in GitHub Actions and, if they pass, deploys to the
  VPS over SSH (`SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY` repository secrets).
- `PIP_INDEX_URL` can point image builds at a faster PyPI mirror when the build host has a slow
  connection.

## Project structure

```text
backend/
  app/            # api, core, db, models, repositories, schemas, services
  tests/          # API, service and cleanup tests
frontend/         # static pages, Nginx configs
docker-compose.yml, docker-compose.dev.yml
Makefile
.github/workflows/deploy.yml
```

## Known limitations and ideas

- No user accounts or file deletion by the owner yet.
- No rate limiting.
- Tables are created on startup; Alembic migrations are not set up yet.
- Tests run on SQLite; running them against PostgreSQL in CI is planned.

## Author

Dzmitry Yurashevich - [GitHub](https://github.com/m3wory)
