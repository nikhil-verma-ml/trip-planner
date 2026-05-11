from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import plan, status
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Travel Planner API",
    description="Backend API for the CrewAI Travel Planner",
    version="1.0.0"
)

# CORS configuration for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(plan.router, prefix="/api", tags=["Planning"])
app.include_router(status.router, prefix="/api", tags=["Status"])

@app.get("/")
async def root():
    return {"message": "AI Travel Planner API is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
