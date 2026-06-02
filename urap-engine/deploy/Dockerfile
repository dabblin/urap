FROM python:3.12-slim

LABEL org.opencontainers.image.title="urap-engine" \
      org.opencontainers.image.vendor="Antigravity (Dabblin Cloud Technologies)" \
      org.opencontainers.image.description="URAP FastAPI microservice — Unified Revenue Acceleration Platform"

WORKDIR /app

# Install dependencies first — cached layer unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user (Cloud Run security best practice)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Cloud Run injects PORT env var; default to 8080
ENV PORT=8080
EXPOSE $PORT

# Health check — uvicorn must be ready before traffic is routed
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c \
  "import httpx,os; r=httpx.get(f'http://localhost:{os.getenv(\"PORT\",\"8080\")}/health',timeout=3); r.raise_for_status()"

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]
