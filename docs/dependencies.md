# Dependencies

All dependencies are declared in `pyproject.toml`.

### FastAPI and validation

- `fastapi` – Handles the 3 CDMS endpoints and 6 emulator endpoints. It generates OpenAPI docs, so I can try the APIs directly through Swagger.
- `uvicorn[standard]` – Runs the FastAPI apps.
- `pydantic` – Validates incoming payloads. `AwareDatetime` rejects timestamps without a timezone before they reach the comparison logic.
- `pydantic-settings` – Loads settings from `.env`. Missing required settings cause the app to fail at startup.

### Database

- `sqlalchemy` – Used for ORM and SQL Core. I also need raw SQL for `pg_advisory_xact_lock` and manual transaction control.
- `psycopg[binary]` – PostgreSQL driver. The binary package includes the client library, so the Docker image doesn't need extra build tools.
- `alembic` – Handles CDMS database migrations. The emulator doesn't use migrations.

### External services and files

- `httpx` – Calls the inventory API and sends requests in the load test. Supports both sync and async requests.
- `openpyxl` – Reads `.xlsx` files. Read-only mode avoids loading the whole workbook into memory.
- `python-multipart` – Required by FastAPI to receive file uploads.

### Seeding and tests

- `faker` – Generates sample products for the emulator. It's a runtime
  dependency rather than a dev one because the seed script ships in the
  Docker image. The exercise asks for this library by name.
- `pytest` – Runs the 22 tests. The only dev-only dependency.

---

Dependencies are managed with [uv](https://docs.astral.sh/uv/).
`uv.lock` pins the resolved tree across platforms, and the Docker build
runs `uv sync --frozen`, which fails if the lockfile and `pyproject.toml`
have drifted.

Everything here comes from PyPI through `pyproject.toml`. No source code was copied from other projects.