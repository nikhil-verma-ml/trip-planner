"""
Flask API backend for the AI Trip Planner frontend.
Exposes the 6-agent CrewAI pipeline over HTTP.

Run:
    pip install flask flask-cors
    python app.py
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
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ── Create output folder at startup ──────────────────────────────────────────
import pathlib
pathlib.Path(os.path.join(_BASE, "output")).mkdir(parents=True, exist_ok=True)
log.info(f"Output folder ready: {os.path.join(_BASE, 'output')}")

# ── In-memory job store ───────────────────────────────────────────────────────
# IMPORTANT: This dict is process-scoped.
# Flask debug=True uses a Werkzeug reloader that forks TWO processes.
# The parent process stores jobs; child process handles requests → always 404.
# FIX: run with use_reloader=False (see bottom of file).
jobs: dict = {}
jobs_lock = threading.Lock()          # thread-safe reads/writes


# ── Pipeline worker ───────────────────────────────────────────────────────────

def run_pipeline_job(job_id: str, trip_details: dict) -> None:
    """
    Run the CrewAI pipeline in a background thread.
    Auto-retries up to 3 times on rate-limit (429) errors with backoff.
    """
    log.info(f"[{job_id}] Pipeline started")

    with jobs_lock:
        jobs[job_id]["status"] = "running"

    MAX_RETRIES = 3
    BACKOFF     = [30, 60, 90]   # seconds to wait before each retry

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from crew import run_trip_planner
            result = run_trip_planner(trip_details)

            with jobs_lock:
                jobs[job_id]["status"] = "done"
                jobs[job_id]["result"] = result
            log.info(f"[{job_id}] Pipeline finished successfully (attempt {attempt})")
            return   # success — exit retry loop

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
                # Non-rate-limit error OR exhausted retries
                log.error(f"[{job_id}] Pipeline failed after {attempt} attempt(s): {e}", exc_info=True)
                with jobs_lock:
                    jobs[job_id]["status"] = "error"
                    jobs[job_id]["error"]  = err_str
                return


# ── Routes ────────────────────────────────────────────────────────────────────


# ── City → IATA / Station code lookup ────────────────────────────────────────
# Common Indian + international airport IATA codes
CITY_TO_IATA = {
    # India
    "new delhi": "DEL", "delhi": "DEL", "indira gandhi": "DEL",
    "mumbai": "BOM", "bombay": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR",
    "hyderabad": "HYD", "kolkata": "CCU", "calcutta": "CCU",
    "chennai": "MAA", "madras": "MAA",
    "ahmedabad": "AMD", "pune": "PNQ", "goa": "GOI",
    "jaipur": "JAI", "lucknow": "LKO", "kochi": "COK",
    "amritsar": "ATQ", "varanasi": "VNS", "bhubaneswar": "BBI",
    "chandigarh": "IXC", "srinagar": "SXR", "leh": "IXL",
    # International
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

# Common Indian railway station codes
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
    """Convert city name to IATA airport code."""
    city_lower = city.lower().strip()
    # Direct match
    for k, v in CITY_TO_IATA.items():
        if k in city_lower or city_lower in k:
            return v
    # Fallback: return first 3 letters uppercased (Amadeus/Serper will handle it)
    words = city.strip().split()
    return words[0][:3].upper() if words else "DEL"


def city_to_station(city: str) -> str:
    """Convert city name to Indian railway station code."""
    city_lower = city.lower().strip()
    for k, v in CITY_TO_STATION.items():
        if k in city_lower or city_lower in k:
            return v
    words = city.strip().split()
    return words[0][:4].upper() if words else "NDLS"


@app.route("/api/plan", methods=["POST"])
def plan():
    """
    Start a trip planning job.

    Body (JSON):
        destination, origin_city, travel_dates, num_travellers,
        budget_inr, interests, travel_mode, origin_iata, dest_iata,
        origin_station, dest_station, date_yyyymmdd

    Returns: { "job_id": "job_YYYYMMDDHHMMSSXXXXXX" }
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Empty or invalid JSON body"}), 400

    destination  = str(data.get("destination",  "Paris, France"))
    origin_city  = str(data.get("origin_city",  "New Delhi"))
    travel_mode  = str(data.get("travel_mode",  "flight"))
    dep_date_raw = str(data.get("dep_date",     datetime.now().strftime("%Y-%m-%d")))
    date_ymd     = dep_date_raw.replace("-", "")

    # Auto-derive IATA and station codes from city names — user never needs to type these
    auto_origin_iata    = city_to_iata(origin_city)
    auto_dest_iata      = city_to_iata(destination)
    auto_origin_station = city_to_station(origin_city)
    auto_dest_station   = city_to_station(destination)

    log.info(f"Auto-resolved: {origin_city} → IATA:{auto_origin_iata} / STN:{auto_origin_station}")
    log.info(f"Auto-resolved: {destination} → IATA:{auto_dest_iata} / STN:{auto_dest_station}")

    trip_details = {
        "destination":    destination,
        "origin_city":    origin_city,
        "travel_dates":   str(data.get("travel_dates",   "")),
        "num_travellers": int(data.get("num_travellers", 2)),
        "budget_inr":     int(data.get("budget_inr",     150000)),
        "interests":      str(data.get("interests",      "sightseeing, food")),
        "travel_mode":    travel_mode,
        "origin_iata":    auto_origin_iata,
        "dest_iata":      auto_dest_iata,
        "origin_station": auto_origin_station,
        "dest_station":   auto_dest_station,
        "date_yyyymmdd":  date_ymd,
    }

    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Store job BEFORE starting thread — avoids race condition
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

    return jsonify({"job_id": job_id}), 202


@app.route("/api/status/<job_id>", methods=["GET"])
def status(job_id: str):
    """
    Poll job status.
    Returns: { "status": "queued|running|done|error", "result": "...", "error": "..." }
    """
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        # Debug info to help diagnose stale job_id issues
        with jobs_lock:
            known = list(jobs.keys())
        log.warning(f"Job not found: {job_id} | Known jobs: {known}")
        return jsonify({
            "error":      "Job not found",
            "job_id":     job_id,
            "known_jobs": known,   # helpful during development
        }), 404

    return jsonify(job)


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """List all jobs (dev helper endpoint)."""
    with jobs_lock:
        return jsonify({
            "count": len(jobs),
            "jobs":  {jid: {"status": j["status"], "created": j.get("created")}
                      for jid, j in jobs.items()},
        })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":    "ok",
        "timestamp": datetime.now().isoformat(),
        "jobs_in_memory": len(jobs),
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Starting VoyageAI Flask backend on http://localhost:5000")
    log.info("Jobs store is process-scoped — do NOT run with use_reloader=True")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False,    # ← THE KEY FIX: prevents Werkzeug from forking
        threaded=True,         # allow concurrent poll requests during pipeline run
    )