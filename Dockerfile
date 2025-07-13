# Multi-stage build for optimization
FROM python:alpine@sha256:b4d299311845147e7e47c970566906caf8378a1f04e5d3de65b5f2e834f8e3bf AS builder

# Install build dependencies
RUN apk add --no-cache \
  gcc \
  musl-dev \
  libffi-dev \
  openssl-dev \
  postgresql-dev \
  python3-dev \
  curl

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements-prod.txt

# Production stage
FROM python:alpine@sha256:b4d299311845147e7e47c970566906caf8378a1f04e5d3de65b5f2e834f8e3bf

# Install runtime dependencies only
RUN apk add --no-cache \
  libpq \
  curl \
  && rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Reduce unnecessary automatic behavior in immutable containers
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1

RUN addgroup -S appuser && adduser -S -G appuser appuser

WORKDIR /app

COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
