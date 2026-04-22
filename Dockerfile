# ── Base image ─────────────────────────────────────────────
FROM python:3.11-slim

# ── System deps ────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────
WORKDIR /app

# ── Install Python deps (cached layer) ────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ─────────────────────────────────────
COPY . .

# ── Create output directory ────────────────────────────────
RUN mkdir -p /app/output

# ── Expose port ────────────────────────────────────────────
EXPOSE 8000

# ── Start with Gunicorn (production WSGI server) ──────────
# 1 worker because CrewAI jobs store state in-memory
# If you need multiple workers, use Redis for job storage
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--threads", "8", \
     "--timeout", "600", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
