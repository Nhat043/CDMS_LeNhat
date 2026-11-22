# CDMS_LeNhat

Change Data Management Service. Tracks product data changes from an inventory service through three channels: scheduled polling, webhooks, and Excel uploads.

Job test for kSynerX. See [docs/](docs/) for the API analysis and design decisions.

## Running with Docker

```bash
docker compose up --build
docker compose exec inventory python -m scripts.seed 20
```

| | |
|---|---|
| Inventory emulator | http://127.0.0.1:8001/docs |
| CDMS | http://127.0.0.1:8002/docs |

The worker polls every 30 seconds. Watch it with
`docker compose logs -f worker`.

## Trying the three channels

**Polling** happens on its own. Change a product in the emulator and the
next cycle picks it up.

**Webhook** - the callback client reads a product and pushes it:

```bash
docker compose exec worker python -m scripts.callback_client PARTNER00003
```

**Excel**:

```bash
docker compose exec cdms python -m scripts.make_excel
docker compose exec cdms curl -s -X POST \
  http://localhost:8002/cdms/v1/imports/products -F "file=@sample-import.xlsx"
```

Then `GET /cdms/v1/imports/{batchId}` for per-row results.

## Taking a service down

Each service has its own database, so one can fail on its own:

```bash
docker compose stop inventory-db
```

Polling starts failing but the worker keeps draining the inbox, so
webhooks and uploads are unaffected. `docker compose start inventory-db`
and the next cycle recovers by itself.

## Running without Docker

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

Then three processes:

```bash
uv run uvicorn app.inventory_main:app --port 8001
uv run uvicorn app.cdms_main:app --port 8002
uv run python -m app.worker_main
```

## Tests

```bash
uv run pytest -q
```

Swagger: http://127.0.0.1:8001/docs

## Layout

| Path | Description |
|---|---|
| `app/core` | Configuration and database connections |
| `app/inventory` | Vietful API emulator |
| `app/cdms/changelog.py` | normalise, hash, decide - no database, no HTTP |
| `app/cdms/processor.py` | applies one event to the state and change log |
| `app/cdms/channels` | webhook, polling, Excel upload |
| `app/worker_main.py` | one loop: schedules polls, drains the inbox |
| `migrations` | CDMS database migrations |
| `docs` | API analysis and design decisions |