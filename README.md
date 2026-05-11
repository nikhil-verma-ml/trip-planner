<div align="center">

# 🌍✈️ AI Travel Planner

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=00D4FF&center=true&vCenter=true&width=600&lines=6+AI+Agents+Planning+Your+Perfect+Trip;FastAPI+%2B+CrewAI+%2B+Real+APIs;Live+on+Render+%26+Vercel!" alt="Typing SVG" />

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-FF6B6B?style=for-the-badge&logo=robot&logoColor=white)](https://crewai.com/)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/)

<br/>

> **An autonomous 6-agent AI pipeline that researches destinations, checks weather, finds hotels, compares ticket prices, and generates complete day-by-day travel itineraries — fully automated.**

<br/>

🔴 **[Live Demo](https://your-app.vercel.app)** &nbsp;|&nbsp; 📖 **[API Docs](https://your-backend.onrender.com/docs)** &nbsp;|&nbsp; ⭐ **Star this repo if you find it useful!**

</div>

---

## 🤖 Meet the 6 AI Agents

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   🔍 Destination    🌤️ Weather      🏨 Hotel        🎫 Ticket      │
│     Researcher       Checker         Finder          Finder         │
│         │               │               │               │           │
│         └───────────────┴───────────────┴───────────────┘           │
│                                 │                                   │
│                    🗓️ Itinerary Planner                             │
│                                 │                                   │
│                    💰 Budget Estimator                              │
│                                                                     │
│              ✅ Complete Travel Guide Generated!                    │
└─────────────────────────────────────────────────────────────────────┘
```

| Agent | Role | APIs Used |
|:---:|---|---|
| 🔍 **Destination Researcher** | Deep-dives into destination info, culture, must-visits | Serper + Gemini |
| 🌤️ **Weather Checker** | Fetches real forecast for travel dates | OpenWeather API |
| 🏨 **Hotel Finder** | Searches & compares hotels by budget | Serper + Gemini |
| 🎫 **Ticket Finder** | Finds flights AND train options, compares prices | Amadeus + Indian Railways |
| 🗓️ **Itinerary Planner** | Creates detailed day-by-day travel plan | Gemini |
| 💰 **Budget Estimator** | Calculates full trip cost with breakdown | Gemini |

---

## 🏗️ Architecture

```
                    ┌──────────────┐
                    │   User 🧑   │
                    └──────┬───────┘
                           │ HTTP Request
                    ┌──────▼───────┐
                    │   Vercel     │  ← Frontend
                    │  (HTML/JS)   │
                    └──────┬───────┘
                           │ REST API
                    ┌──────▼───────┐
                    │    Render    │  ← Backend
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │    CrewAI Pipeline      │
              │  Agent 1 → 2 → 3 → 4   │
              │       → 5 → 6          │
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼────┐      ┌─────▼─────┐
   │ Gemini  │       │ Amadeus  │      │OpenWeather│
   │   API   │       │   API    │      │    API    │
   └─────────┘       └──────────┘      └───────────┘
```

---

## 📁 Project Structure

```
trip_planner/
│
├── 🔧 backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + CORS
│   │   ├── routes/
│   │   │   ├── plan.py          # POST /api/plan
│   │   │   └── status.py        # GET  /api/status/{job_id}
│   │   ├── agents/              # 6 CrewAI Agents
│   │   │   ├── destination_researcher.py
│   │   │   ├── weather_checker.py
│   │   │   ├── hotel_finder.py
│   │   │   ├── ticket_finder.py
│   │   │   ├── itinerary_planner.py
│   │   │   └── budget_estimator.py
│   │   ├── tasks/               # CrewAI Task definitions
│   │   ├── tools/               # Custom API tools
│   │   │   ├── weather_tool.py  # OpenWeather wrapper
│   │   │   ├── amadeus_tool.py  # Flight search
│   │   │   └── railway_tool.py  # Indian Railways
│   │   └── crew.py              # Pipeline orchestration
│   ├── requirements.txt
│   ├── Procfile                 # Render deployment
│   └── railway.json
│
├── 🎨 frontend/
│   ├── index.html
│   └── assets/
│       ├── css/style.css        # Glassmorphism UI
│       └── js/
│           ├── main.js          # API calls + logic
│           ├── pipeline.js      # Agent progress animation
│           └── markdown.js      # Itinerary renderer
│
├── 🐳 docker-compose.yml        # Local dev
└── 📖 README.md
```

---

## ⚡ Quick Start

### Option 1 — Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/nikhil-verma-ml/trip-planner.git
cd trip-planner

# Add your API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

# Run everything
docker-compose up
```

🌐 Frontend: `http://localhost:3000`  
🔌 Backend:  `http://localhost:8000`  
📖 API Docs: `http://localhost:8000/docs`

---

### Option 2 — Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
# Open index.html with Live Server (VS Code extension)
# OR
python -m http.server 3000
```

---

## 🔑 Environment Variables

Create `backend/.env` file:

```env
# 🤖 AI
GEMINI_API_KEY=your_gemini_key

# 🔍 Search
SERPER_API_KEY=your_serper_key

# 🌤️ Weather
OPENWEATHER_API_KEY=your_openweather_key

# ✈️ Flights
AMADEUS_CLIENT_ID=your_amadeus_id
AMADEUS_CLIENT_SECRET=your_amadeus_secret
```

> 💡 All APIs have **free tiers** — no credit card required to get started!

---

## 🌐 API Reference

### `POST /api/plan`
Trigger a new AI trip planning job.

```json
// Request Body
{
  "destination": "Goa",
  "days": 5,
  "budget": "medium",
  "travel_mode": "flight",
  "from_city": "Delhi"
}

// Response
{
  "job_id": "abc123",
  "status": "started"
}
```

### `GET /api/status/{job_id}`
Poll for results.

```json
// Response (when complete)
{
  "status": "completed",
  "result": "# 5-Day Goa Travel Guide\n..."
}
```

### `GET /docs`
Interactive Swagger UI — test all endpoints directly in browser.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 1.5 Pro |
| **Agent Framework** | CrewAI |
| **Backend** | FastAPI + Uvicorn |
| **Async Jobs** | Python Background Tasks |
| **Frontend** | Vanilla JS + CSS (Glassmorphism) |
| **Flight Search** | Amadeus API |
| **Train Search** | Indian Railways API |
| **Weather** | OpenWeatherMap API |
| **Web Search** | Serper API |
| **Backend Deploy** | Render |
| **Frontend Deploy** | Vercel |
| **Local Dev** | Docker Compose |

---

## ✨ Key Features

- 🤖 **6 Autonomous Agents** — each specialized, working in sequence
- ⛓️ **Context Chaining** — each agent gets all previous agents' output
- 🎫 **Multi-modal Transport** — flight, train, or both
- 💰 **Real Price Data** — actual Amadeus flight prices
- 🌤️ **Live Weather** — real forecast for travel dates
- 📊 **Budget Breakdown** — per-day cost estimates
- 📋 **Markdown Output** — beautifully formatted travel guide
- 🔄 **Async Pipeline** — non-blocking, with live progress tracking
- 🛡️ **Demo Mode** — works even if backend is offline

---

<div align="center">

## 🚀 Deployed & Live

[![Frontend](https://img.shields.io/badge/Frontend-Live_on_Vercel-000000?style=for-the-badge&logo=vercel)](https://trip-planner-nu-puce.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Live_on_Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://trip-planner-backend-5v75.onrender.com/docs)

---

Made with ❤️ by [Nikhil Verma](https://github.com/nikhil-verma-ml)

⭐ **Star this repo** if it helped you!

</div>