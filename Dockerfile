# ── Base image ────────────────────────────────────────────
FROM python:3.11-slim

# ── System deps ───────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────
WORKDIR /app

# ── Install Python deps (cached layer) ───────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────
COPY . .

# ── Create output directory ───────────────────────────────
RUN mkdir -p /app/output

# ── Expose port ───────────────────────────────────────────
EXPOSE 8000

# ── FIX: Use shell form so $PORT env var expands correctly ─
# Railway/Render inject $PORT at runtime — exec form ["cmd"] 
# does NOT expand shell variables, shell form does.
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1