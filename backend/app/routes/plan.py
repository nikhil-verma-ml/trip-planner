from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from app.crew import run_trip_planner
from app.state import jobs
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class TripRequest(BaseModel):
    origin_city: str
    destination: str
    travel_dates: str
    date_yyyymmdd: str
    num_travellers: int
    budget_inr: int
    interests: str
    travel_mode: str = "flight"

class PlanResponse(BaseModel):
    job_id: str
    status: str

def execute_crew(job_id: str, trip_details: dict):
    try:
        jobs[job_id]["status"] = "processing"
        result = run_trip_planner(trip_details)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result
    except Exception as e:
        logger.error(f"Error executing CrewAI for job {job_id}: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@router.post("/plan", response_model=PlanResponse)
async def create_plan(request: TripRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    trip_details = request.dict()
    
    jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None
    }
    
    background_tasks.add_task(execute_crew, job_id, trip_details)
    
    return PlanResponse(job_id=job_id, status="queued")
