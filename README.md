# CDMS_LeNhat

Change Data Management Service. Tracks product data changes from an inventory service through three channels: scheduled polling, webhooks, and Excel uploads.

Job test for kSynerX. See [docs/](docs/) for the API analysis and design decisions.

## Setup

Requires Python 3.13, PostgreSQL, and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
copy .env.example .env
```

Add your PostgreSQL password to `.env`, then create the two databases and run migrations:

```bash
psql -U postgres -c "CREATE DATABASE lenhat_inventory;"
psql -U postgres -c "CREATE DATABASE lenhat_cdms;"
uv run alembic upgrade head
```

## Inventory emulator

A small emulator for the Vietful Products API. Its tables are created on startup, so no migrations are needed.

```bash
uv run uvicorn app.inventory_main:app --port 8001
uv run python -m scripts.seed 20
```

Swagger: http://127.0.0.1:8001/docs

## Layout

| Path | Description |
|---|---|
| `app/core` | Configuration and database connections |
| `app/inventory` | Vietful API emulator |
| `app/cdms` | Change detection and ingest channels |
| `migrations` | CDMS database migrations |
| `docs` | API analysis and design decisions |