"""
FastAPI backend for the AI Trip Planner frontend.
Exposes the 6-agent CrewAI pipeline over HTTP.

Run:
    pip install fastapi uvicorn
    uvicorn app:app --reload
"""

import os
import sys

# ── Force project root into sys.path ─────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import threading
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(title="AI Trip Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create output folder at startup ──────────────────────────────────────────
import pathlib
pathlib.Path(os.path.join(_BASE, "output")).mkdir(parents=True, exist_ok=True)
log.info(f"Output folder ready: {os.path.join(_BASE, 'output')}")

# ── In-memory job store ───────────────────────────────────────────────────────
jobs: dict = {}
jobs_lock = threading.Lock()


# ── Pipeline worker ───────────────────────────────────────────────────────────
def run_pipeline_job(job_id: str, trip_details: dict) -> None:
    log.info(f"[{job_id}] Pipeline started")

    with jobs_lock:
        jobs[job_id]["status"] = "running"

    MAX_RETRIES = 3
    BACKOFF     = [30, 60, 90]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from agents.crew import run_trip_planner
            result = run_trip_planner(trip_details)

            with jobs_lock:
                jobs[job_id]["status"] = "done"
                jobs[job_id]["result"] = result
            log.info(f"[{job_id}] Pipeline finished successfully (attempt {attempt})")
            return

        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower() or "RateLimitError" in err_str

            if is_rate_limit and attempt < MAX_RETRIES:
                wait = BACKOFF[attempt - 1]
                log.warning(
                    f"[{job_id}] Rate limit hit (attempt {attempt}/{MAX_RETRIES}). "
                    f"Waiting {wait}s before retry..."
                )
                with jobs_lock:
                    jobs[job_id]["status"] = f"rate_limited – retry {attempt}/{MAX_RETRIES} in {wait}s"

                import time
                time.sleep(wait)
                log.info(f"[{job_id}] Retrying now (attempt {attempt+1})...")

            else:
                log.error(f"[{job_id}] Pipeline failed after {attempt} attempt(s): {e}", exc_info=True)
                with jobs_lock:
                    jobs[job_id]["status"] = "error"
                    jobs[job_id]["error"]  = err_str
                return


# ── City → IATA / Station code lookup ────────────────────────────────────────
CITY_TO_IATA = {
    "new delhi": "DEL", "delhi": "DEL", "indira gandhi": "DEL",
    "mumbai": "BOM", "bombay": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR",
    "hyderabad": "HYD", "kolkata": "CCU", "calcutta": "CCU",
    "chennai": "MAA", "madras": "MAA",
    "ahmedabad": "AMD", "pune": "PNQ", "goa": "GOI",
    "jaipur": "JAI", "lucknow": "LKO", "kochi": "COK",
    "amritsar": "ATQ", "varanasi": "VNS", "bhubaneswar": "BBI",
    "chandigarh": "IXC", "srinagar": "SXR", "leh": "IXL",
    "paris": "CDG", "france": "CDG",
    "london": "LHR", "uk": "LHR", "england": "LHR",
    "dubai": "DXB", "uae": "DXB",
    "singapore": "SIN", "bangkok": "BKK", "thailand": "BKK",
    "new york": "JFK", "usa": "JFK", "america": "JFK",
    "tokyo": "NRT", "japan": "NRT",
    "sydney": "SYD", "australia": "SYD",
    "toronto": "YYZ", "canada": "YYZ",
    "frankfurt": "FRA", "germany": "FRA",
    "amsterdam": "AMS", "netherlands": "AMS",
    "rome": "FCO", "italy": "FCO",
    "barcelona": "BCN", "madrid": "MAD", "spain": "MAD",
    "doha": "DOH", "qatar": "DOH",
    "abu dhabi": "AUH",
    "kuala lumpur": "KUL", "malaysia": "KUL",
    "hong kong": "HKG", "seoul": "ICN", "korea": "ICN",
    "beijing": "PEK", "china": "PEK", "shanghai": "PVG",
    "nairobi": "NBO", "kenya": "NBO",
    "istanbul": "IST", "turkey": "IST",
    "cairo": "CAI", "egypt": "CAI",
    "johannesburg": "JNB", "south africa": "JNB",
    "kathmandu": "KTM", "nepal": "KTM",
    "colombo": "CMB", "sri lanka": "CMB",
    "dhaka": "DAC", "bangladesh": "DAC",
    "karachi": "KHI", "pakistan": "KHI",
    "muscat": "MCT", "oman": "MCT",
    "zurich": "ZRH", "switzerland": "ZRH",
    "vienna": "VIE", "austria": "VIE",
    "brussels": "BRU", "belgium": "BRU",
    "lisbon": "LIS", "portugal": "LIS",
    "athens": "ATH", "greece": "ATH",
    "prague": "PRG", "czech": "PRG",
    "budapest": "BUD", "hungary": "BUD",
    "warsaw": "WAW", "poland": "WAW",
    "stockholm": "ARN", "sweden": "ARN",
    "oslo": "OSL", "norway": "OSL",
    "copenhagen": "CPH", "denmark": "CPH",
    "helsinki": "HEL", "finland": "HEL",
    "los angeles": "LAX", "san francisco": "SFO",
    "chicago": "ORD", "miami": "MIA",
    "mexico city": "MEX", "mexico": "MEX",
    "sao paulo": "GRU", "brazil": "GRU",
    "buenos aires": "EZE", "argentina": "EZE",
}

CITY_TO_STATION = {
    "new delhi": "NDLS", "delhi": "NDLS",
    "mumbai": "CSTM", "bombay": "BCT", "mumbai central": "BCT",
    "bangalore": "SBC", "bengaluru": "SBC",
    "chennai": "MAS", "madras": "MAS",
    "kolkata": "KOAA", "howrah": "HWH",
    "hyderabad": "HYB", "secunderabad": "SC",
    "ahmedabad": "ADI", "pune": "PUNE",
    "jaipur": "JP", "lucknow": "LKO",
    "varanasi": "BSB", "allahabad": "ALD", "prayagraj": "PRYJ",
    "bhopal": "BPL", "indore": "INDB",
    "nagpur": "NGP", "surat": "ST",
    "chandigarh": "CDG", "amritsar": "ASR",
    "agra": "AGC", "mathura": "MTJ",
    "patna": "PNBE", "guwahati": "GHY",
    "bhubaneswar": "BBS", "visakhapatnam": "VSKP",
    "kochi": "ERS", "thiruvananthapuram": "TVC",
    "coimbatore": "CBE", "madurai": "MDU",
    "mangalore": "MAQ", "goa": "MAO", "madgaon": "MAO",
    "jodhpur": "JU", "udaipur": "UDZ", "ajmer": "AII",
    "shimla": "SML", "dehradun": "DDN",
    "jammu": "JAT", "srinagar": "SRNG",
    "ranchi": "RNC", "raipur": "R",
}

def city_to_iata(city: str) -> str:
    city_lower = city.lower().strip()
    for k, v in CITY_TO_IATA.items():
        if k in city_lower or city_lower in k:
            return v
    words = city.strip().split()
    return words[0][:3].upper() if words else "DEL"

def city_to_station(city: str) -> str:
    city_lower = city.lower().strip()
    for k, v in CITY_TO_STATION.items():
        if k in city_lower or city_lower in k:
            return v
    words = city.strip().split()
    return words[0][:4].upper() if words else "NDLS"

class TripPlanRequest(BaseModel):
    destination: str = "Paris, France"
    origin_city: str = "New Delhi"
    travel_mode: str = "flight"
    dep_date: Optional[str] = None
    travel_dates: Optional[str] = ""
    num_travellers: Optional[int] = 2
    budget_inr: Optional[int] = 150000
    interests: Optional[str] = "sightseeing, food"

@app.post("/api/plan", status_code=202)
def plan(request: TripPlanRequest):
    dep_date_raw = request.dep_date if request.dep_date else datetime.now().strftime("%Y-%m-%d")
    date_ymd = dep_date_raw.replace("-", "")

    auto_origin_iata = city_to_iata(request.origin_city)
    auto_dest_iata = city_to_iata(request.destination)
    auto_origin_station = city_to_station(request.origin_city)
    auto_dest_station = city_to_station(request.destination)

    log.info(f"Auto-resolved: {request.origin_city} → IATA:{auto_origin_iata} / STN:{auto_origin_station}")
    log.info(f"Auto-resolved: {request.destination} → IATA:{auto_dest_iata} / STN:{auto_dest_station}")

    trip_details = {
        "destination":    request.destination,
        "origin_city":    request.origin_city,
        "travel_dates":   request.travel_dates,
        "num_travellers": request.num_travellers,
        "budget_inr":     request.budget_inr,
        "interests":      request.interests,
        "travel_mode":    request.travel_mode,
        "origin_iata":    auto_origin_iata,
        "dest_iata":      auto_dest_iata,
        "origin_station": auto_origin_station,
        "dest_station":   auto_dest_station,
        "date_yyyymmdd":  date_ymd,
    }

    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    with jobs_lock:
        jobs[job_id] = {
            "status":  "queued",
            "result":  None,
            "error":   None,
            "created": datetime.now().isoformat(),
        }

    log.info(f"[{job_id}] Job queued for: {trip_details['destination']}")
    log.info(f"[{job_id}] Total jobs in store: {len(jobs)}")

    thread = threading.Thread(
        target=run_pipeline_job,
        args=(job_id, trip_details),
        daemon=True,
        name=f"pipeline-{job_id}",
    )
    thread.start()

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        with jobs_lock:
            known = list(jobs.keys())
        log.warning(f"Job not found: {job_id} | Known jobs: {known}")
        return JSONResponse(
            status_code=404,
            content={
                "error":      "Job not found",
                "job_id":     job_id,
                "known_jobs": known,
            }
        )

    return job


@app.get("/api/jobs")
def list_jobs():
    with jobs_lock:
        return {
            "count": len(jobs),
            "jobs":  {jid: {"status": j["status"], "created": j.get("created")}
                      for jid, j in jobs.items()},
        }


@app.get("/api/health")
def health():
    return {
        "status":    "ok",
        "timestamp": datetime.now().isoformat(),
        "jobs_in_memory": len(jobs),
    }


# Serve static files last to prevent masking API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    log.info("Starting VoyageAI FastAPI backend")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        reload=False
    )