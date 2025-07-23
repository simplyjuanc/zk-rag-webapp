# Multi-stage build for optimization
FROM python:alpine@sha256:b4d299311845147e7e47c970566906caf8378a1f04e5d3de65b5f2e834f8e3bf AS builder

RUN apk add --no-cache \
  gcc \
  musl-dev \
  libffi-dev \
  openssl-dev \
  postgresql-dev \
  python3-dev \
  curl \
  # Required for building numpy/scipy
  g++ \
  make \
  gfortran \
  openblas-dev

# Copy uv files for dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:alpine@sha256:b4d299311845147e7e47c970566906caf8378a1f04e5d3de65b5f2e834f8e3bf as production

RUN apk add --no-cache \
  libpq \
  curl \
  openblas \
  && rm -rf /var/cache/apk/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Reduce unnecessary automatic behavior in immutable containers
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_SYSTEM_PYTHON=1

RUN addgroup -S appuser && adduser -S -G appuser appuser

WORKDIR /app

COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
