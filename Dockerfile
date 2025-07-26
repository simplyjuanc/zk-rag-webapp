FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  make \
  libpq-dev \
  libffi-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy uv files for dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.11-slim as production

RUN apt-get update && apt-get install -y \
  libpq5 \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Reduce unnecessary automatic behavior in immutable containers
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_SYSTEM_PYTHON=1

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
