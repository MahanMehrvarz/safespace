"""Data models for PractAI system."""
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Stance(str, Enum):
    """Supervisor's overall stance toward the research."""
    SUPPORTIVE = "supportive"
    SKEPTICAL = "skeptical"
    UNCLEAR = "unclear"


class Confidence(str, Enum):
    """Supervisor's confidence in their assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NextMove(str, Enum):
    """Supervisor's intended next action."""
    QUESTION = "question"
    CHALLENGE = "challenge"
    ENCOURAGE = "encourage"


class ImpressionState(BaseModel):
    """Private impression state for each supervisor."""
    stance: Stance
    concerns: List[str] = Field(default_factory=list)
    confidence: Confidence
    next_move: NextMove
    rationale: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    """A message in the conversation."""
    speaker: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    round_number: int
    is_researcher: bool = False


class SupervisorResponse(BaseModel):
    """Complete supervisor response including public and private parts."""
    supervisor_name: str
    public_response: str
    impression: ImpressionState
    references_colleagues: List[str] = Field(default_factory=list)
    round_number: int


class VisibilityReflection(BaseModel):
    """Meta-analysis from the visibility agent."""
    round_number: int
    timestamp: datetime = Field(default_factory=datetime.now)
    analysis: str
    impression_summary: dict  # {supervisor_name: stance}


class SessionMetadata(BaseModel):
    """Metadata about a session."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    current_round: int = 0
    total_messages: int = 0


class SessionState(BaseModel):
    """Complete state of a supervision meeting session."""
    metadata: SessionMetadata
    conversation_history: List[Message] = Field(default_factory=list)
    impression_timeline: dict[str, List[ImpressionState]] = Field(default_factory=dict)
    visibility_reflections: List[VisibilityReflection] = Field(default_factory=list)
    active: bool = True


class SupervisorConfig(BaseModel):
    """Configuration for a supervisor personality."""
    name: str
    role: str
    initial_stance: Stance
    initial_confidence: Confidence
    personality: dict
    focus_areas: List[str] = Field(default_factory=list)
    what_convinces: List[str] = Field(default_factory=list)
    what_increases_skepticism: Optional[List[str]] = None
    what_increases_concerns: Optional[List[str]] = None
