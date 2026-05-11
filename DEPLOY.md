# VoyageAI — Deployment Guide

Complete guide to host this project for FREE on 3 platforms.

---

## Option A — Railway.app (Recommended ⭐)

**Free tier:** $5 credit/month (enough for ~500 hours) | Docker support | Auto-deploy from GitHub

### Steps:
```bash
# 1. Push your code to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/voyageai.git
git push -u origin main

# 2. Go to railway.app → New Project → Deploy from GitHub repo
# 3. Select your repo → Railway auto-detects Dockerfile
# 4. Go to Variables tab → Add all API keys:
```

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | your key |
| `SERPER_API_KEY` | your key |
| `OPENWEATHER_API_KEY` | your key |
| `GEMINI_API_KEY` | your key |
| `RAPIDAPI_KEY` | your key |
| `AVIATIONSTACK_API_KEY` | your key |

```
# 5. Click Deploy → Railway gives you a public URL like:
#    https://voyageai-production.up.railway.app
```

---

## Option B — Render.com

**Free tier:** 750 hours/month | Sleeps after 15 min inactivity | No Docker needed

### Steps:
```
1. Push code to GitHub (same as above)
2. render.com → New → Web Service → Connect GitHub repo
3. Settings auto-filled from render.yaml file
4. Go to Environment tab → Add all API keys (same as above)
5. Click Deploy → URL: https://voyageai.onrender.com
```

> ⚠️ Free tier sleeps after 15 min — first request after sleep takes ~30 seconds.
> To avoid this, upgrade to Starter ($7/month) or use Railway instead.

---

## Option C — Local Docker (Your Own Server / VPS)

**Cost:** Free if you have a server (DigitalOcean $4/mo, AWS EC2 free tier)

```bash
# 1. Install Docker on your server
curl -fsSL https://get.docker.com | sh

# 2. Clone your repo
git clone https://github.com/YOUR_USERNAME/voyageai.git
cd voyageai

# 3. Create .env with your API keys
cp .env.example .env
nano .env   # fill in your keys

# 4. Build and run
docker compose up -d

# 5. Access at http://YOUR_SERVER_IP:8000
# 6. Check logs
docker compose logs -f
```

---

## Option D — Fly.io

**Free tier:** 3 shared VMs, 160 GB bandwidth/month

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch          # auto-detects Dockerfile
fly secrets set GROQ_API_KEY=your_key
fly secrets set SERPER_API_KEY=your_key
fly secrets set OPENWEATHER_API_KEY=your_key
fly secrets set GEMINI_API_KEY=your_key
fly deploy

# URL: https://voyageai.fly.dev
```

---

## File Structure for Deployment

```
trip_planner/
├── Dockerfile          ← Docker image definition
├── docker-compose.yml  ← Local Docker run config
├── Procfile            ← Render / Heroku start command
├── render.yaml         ← Render auto-config
├── railway.json        ← Railway auto-config
├── .gitignore          ← Excludes .env and __pycache__
├── .dockerignore       ← Excludes .env from Docker image
├── .env.example        ← API key template (commit this)
├── .env                ← Your actual keys (NEVER commit)
├── requirements.txt    ← Python dependencies
├── app.py              ← FastAPI backend (serves frontend too)
├── crew.py             ← CrewAI pipeline
├── agents/             ← 6 agent definitions
├── tasks/              ← Task definitions
├── tools/              ← API tool wrappers
└── frontend/
    └── index.html      ← Served at / by FastAPI
```

---

## Important Notes

**1. Workers must be 1**
CrewAI job state is stored in-memory. Multiple workers would lose job IDs.
The Uvicorn command uses `--workers 1` — do NOT change this.

**2. Pipeline Execution Time**
The 6-agent pipeline can take 5–10 minutes. Uvicorn default behavior should handle this, but be aware that some free hosting providers may have reverse proxy timeouts.

**3. .env file is NEVER committed**
`.gitignore` and `.dockerignore` both exclude `.env`.
Always set environment variables through the platform's dashboard.

**4. Output folder**
Travel guides are saved to `/app/output/` inside the container.
On Railway/Render these are ephemeral (lost on redeploy).
For permanent storage, integrate S3 or Google Drive.

---

## Quick Test After Deploy

Visit your URL → you should see the VoyageAI form.
Click the health endpoint to confirm backend is running:
```
https://YOUR_URL/api/health
```
Expected response:
```json
{"status": "ok", "timestamp": "2026-...", "jobs_in_memory": 0}
```
