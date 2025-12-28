"""FastAPI backend for PractAI."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict
import os
from pathlib import Path

from config.loader import load_supervisor_configs
from config.llm_provider import get_llm
from agents.meeting import MeetingOrchestrator

# Initialize FastAPI
app = FastAPI(title="PractAI", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
orchestrator: Optional[MeetingOrchestrator] = None


# Request/Response models
class StartSessionRequest(BaseModel):
    session_id: Optional[str] = None


class StartSessionResponse(BaseModel):
    session_id: str
    supervisors: list[Dict[str, str]]


class ResearcherInputRequest(BaseModel):
    input: str
    request_reflection: bool = False


class ResearcherInputResponse(BaseModel):
    round_number: int
    supervisor_responses: list[Dict]
    current_impressions: Dict[str, Dict]
    visibility_reflection: Optional[Dict]


@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global orchestrator

    # Load supervisor configurations
    supervisor_configs = load_supervisor_configs("config/supervisors.yaml")

    # Get LLM with slightly higher temperature to reduce repetition
    llm = get_llm(temperature=0.9)

    # Get meeting parameters from env
    cross_talk_prob = float(os.getenv("CROSS_TALK_PROBABILITY", "0.3"))
    checkpoint_interval = int(os.getenv("VISIBILITY_CHECKPOINT_INTERVAL", "3"))

    # Initialize orchestrator
    orchestrator = MeetingOrchestrator(
        supervisor_configs=supervisor_configs,
        llm=llm,
        cross_talk_probability=cross_talk_prob,
        visibility_checkpoint_interval=checkpoint_interval,
    )

    print(f"✅ PractAI initialized with {len(supervisor_configs)} supervisors")
    print(f"   Cross-talk probability: {cross_talk_prob}")
    print(f"   Visibility checkpoints every {checkpoint_interval} rounds")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend."""
    frontend_path = Path("frontend/index.html")
    if frontend_path.exists():
        return frontend_path.read_text()
    return "<h1>PractAI</h1><p>Frontend not found. Please check frontend/index.html</p>"


@app.post("/api/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """Start a new supervision meeting session."""
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="System not initialized")

    session_id = orchestrator.start_session(request.session_id)

    supervisors = [
        {"name": config.name, "role": config.role}
        for config in orchestrator.supervisor_configs
    ]

    return StartSessionResponse(
        session_id=session_id,
        supervisors=supervisors,
    )


@app.post("/api/session/input", response_model=ResearcherInputResponse)
async def process_input(request: ResearcherInputRequest):
    """Process researcher input and get supervisor responses."""
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="System not initialized")

    if orchestrator.current_session is None:
        raise HTTPException(status_code=400, detail="No active session. Start a session first.")

    result = await orchestrator.process_researcher_input(
        researcher_input=request.input,
        request_reflection=request.request_reflection,
    )

    return ResearcherInputResponse(**result)


@app.get("/api/session/export")
async def export_session():
    """Export current session data."""
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="System not initialized")

    if orchestrator.current_session is None:
        raise HTTPException(status_code=400, detail="No active session")

    return orchestrator.export_session()


@app.post("/api/session/end")
async def end_session():
    """End the current session."""
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="System not initialized")

    orchestrator.end_session()
    return {"status": "Session ended"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "has_active_session": orchestrator.current_session is not None if orchestrator else False,
    }


# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if not frontend_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    with open(frontend_path, "r") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
