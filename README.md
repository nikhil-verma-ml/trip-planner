# AI Travel Planner (CrewAI + FastAPI)

Professional AI-powered travel planning application built with **CrewAI** (6 specialized agents) and **FastAPI**.

## Project Architecture

- **Backend**: FastAPI with async background tasks for long-running AI pipelines.
- **Frontend**: Modern Vanilla JS/CSS with glassmorphism and real-time progress visualization.
- **Deployment**: Configured for Railway (Backend) and Vercel (Frontend).

## Project Structure

```text
backend/
  app/
    main.py              # FastAPI entry point
    routes/              # API endpoints (plan, status)
    agents/              # CrewAI Agents (6 specialized roles)
    tasks/               # CrewAI Tasks
    tools/               # Custom tools (Weather, Flights, etc.)
    crew.py              # Pipeline orchestration
  requirements.txt
  Procfile               # Railway deployment
  railway.json

frontend/
  index.html
  assets/
    css/style.css
    js/                  # Frontend logic & animations
  vercel.json            # Vercel deployment

docker-compose.yml       # Local development
```

## Getting Started

### Local Development (Docker)

1. Create a `.env` file in the root with your API keys (see `backend/.env.example`).
2. Run `docker-compose up`.
3. Frontend: `http://localhost:3000`
4. Backend: `http://localhost:8000`

### Local Development (Manual)

**Backend:**
1. `cd backend`
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`

**Frontend:**
1. Open `frontend/index.html` in a live server.

## API Endpoints

- `POST /api/plan`: Trigger a new trip planning job.
- `GET /api/status/{job_id}`: Check status and get results of a job.
- `GET /docs`: Swagger UI documentation.
