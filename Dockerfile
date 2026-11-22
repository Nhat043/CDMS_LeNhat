FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencies first so they stay cached when only the code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY app/ ./app/
COPY scripts/ ./scripts/

ENV PATH="/app/.venv/bin:$PATH"