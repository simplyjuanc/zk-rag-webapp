FROM python:alpine@sha256:452682e4648deafe431ad2f2391d726d7c52f0ff291be8bd4074b10379bb89ff

# Reduce unnecessary automatic behavior in immutable containers
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user to change to later
RUN addgroup -S appuser && adduser -S -G appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
