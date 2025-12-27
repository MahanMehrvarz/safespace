"""Meeting orchestration with LangGraph."""
import random
import uuid
from typing import List, Optional, Dict, TypedDict, Annotated
from datetime import datetime
from operator import add

from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseChatModel

from models.schemas import (
    SessionState,
    SessionMetadata,
    Message,
    ImpressionState,
    VisibilityReflection,
    SupervisorConfig,
)
from agents.supervisor import SupervisorAgent
from agents.visibility import VisibilityAgent


class MeetingState(TypedDict):
    """State for the meeting graph."""
    session_id: str
    round_number: int
    researcher_input: str
    supervisor_responses: Annotated[List[str], add]  # Accumulate responses
    messages: Annotated[List[Message], add]
    impression_timeline: Dict[str, List[ImpressionState]]
    visibility_reflections: Annotated[List[VisibilityReflection], add]
    should_reflect: bool
    cross_talk_enabled: bool


class MeetingOrchestrator:
    """
    Orchestrates supervision meeting with LangGraph.

    Key features:
    - Memory isolation between supervisors
    - Probabilistic cross-talk
    - Automatic visibility checkpoints
    """

    def __init__(
        self,
        supervisor_configs: List[SupervisorConfig],
        llm: BaseChatModel,
        cross_talk_probability: float = 0.3,
        visibility_checkpoint_interval: int = 3,
    ):
        self.supervisor_configs = supervisor_configs
        self.cross_talk_probability = cross_talk_probability
        self.visibility_checkpoint_interval = visibility_checkpoint_interval

        # Initialize agents
        self.supervisors: Dict[str, SupervisorAgent] = {
            config.name: SupervisorAgent(config, llm)
            for config in supervisor_configs
        }
        self.visibility_agent = VisibilityAgent(llm)

        # Session state
        self.current_session: Optional[SessionState] = None

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new supervision meeting session."""
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        metadata = SessionMetadata(
            session_id=session_id,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            current_round=0,
            total_messages=0,
        )

        self.current_session = SessionState(
            metadata=metadata,
            conversation_history=[],
            impression_timeline={sup.name: [] for sup in self.supervisor_configs},
            visibility_reflections=[],
            active=True,
        )

        return session_id

    async def process_researcher_input(
        self,
        researcher_input: str,
        request_reflection: bool = False,
    ) -> Dict:
        """
        Process researcher input and generate supervisor responses.

        Args:
            researcher_input: What the researcher said
            request_reflection: Force visibility reflection this round

        Returns:
            Dict with supervisor_responses and optional visibility_reflection
        """
        if not self.current_session:
            raise ValueError("No active session. Call start_session() first.")

        # Increment round
        self.current_session.metadata.current_round += 1
        round_number = self.current_session.metadata.current_round

        # Add researcher message to history
        researcher_message = Message(
            speaker="Researcher",
            content=researcher_input,
            round_number=round_number,
            is_researcher=True,
        )
        self.current_session.conversation_history.append(researcher_message)
        self.current_session.metadata.total_messages += 1

        # Collect supervisor responses
        supervisor_responses = []
        current_impressions = {}

        for i, supervisor in enumerate(self.supervisors.values()):
            # Determine cross-talk
            enable_cross_talk = random.random() < self.cross_talk_probability

            # Provide colleague responses if cross-talk enabled
            colleague_responses = None
            if enable_cross_talk and supervisor_responses:
                # Give this supervisor access to previous supervisors' responses this round
                colleague_responses = [
                    (resp.supervisor_name, resp.public_response)
                    for resp in supervisor_responses
                ]

            # Get supervisor response
            response = await supervisor.respond(
                researcher_input=researcher_input,
                round_number=round_number,
                colleague_responses=colleague_responses,
                conversation_history=self.current_session.conversation_history,
            )

            supervisor_responses.append(response)

            # Add to conversation history
            supervisor_message = Message(
                speaker=supervisor.name,
                content=response.public_response,
                round_number=round_number,
                is_researcher=False,
            )
            self.current_session.conversation_history.append(supervisor_message)
            self.current_session.metadata.total_messages += 1

            # Track impression
            self.current_session.impression_timeline[supervisor.name].append(
                response.impression
            )
            current_impressions[supervisor.name] = response.impression

        # Update session timestamp
        self.current_session.metadata.last_updated = datetime.now()

        # Check if we should generate visibility reflection
        should_reflect = (
            request_reflection or
            (round_number % self.visibility_checkpoint_interval == 0)
        )

        visibility_reflection = None
        if should_reflect:
            visibility_reflection = await self.visibility_agent.generate_reflection(
                conversation_history=self.current_session.conversation_history,
                current_impressions=current_impressions,
                impression_timeline=self.current_session.impression_timeline,
                round_number=round_number,
            )
            self.current_session.visibility_reflections.append(visibility_reflection)

        return {
            "round_number": round_number,
            "supervisor_responses": [
                {
                    "name": resp.supervisor_name,
                    "response": resp.public_response,
                    "references": resp.references_colleagues,
                }
                for resp in supervisor_responses
            ],
            "current_impressions": {
                name: {
                    "stance": impression.stance.value,
                    "confidence": impression.confidence.value,
                    "concerns": impression.concerns,
                    "next_move": impression.next_move.value,
                }
                for name, impression in current_impressions.items()
            },
            "visibility_reflection": {
                "analysis": visibility_reflection.analysis,
                "impression_summary": visibility_reflection.impression_summary,
            } if visibility_reflection else None,
        }

    def get_session_state(self) -> Optional[SessionState]:
        """Get current session state."""
        return self.current_session

    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.active = False

    def export_session(self) -> dict:
        """Export session data for analysis."""
        if not self.current_session:
            return {}

        return {
            "session_id": self.current_session.metadata.session_id,
            "created_at": self.current_session.metadata.created_at.isoformat(),
            "total_rounds": self.current_session.metadata.current_round,
            "total_messages": self.current_session.metadata.total_messages,
            "conversation": [
                {
                    "round": msg.round_number,
                    "speaker": msg.speaker,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in self.current_session.conversation_history
            ],
            "impression_timeline": {
                name: [
                    {
                        "stance": imp.stance.value,
                        "confidence": imp.confidence.value,
                        "concerns": imp.concerns,
                        "next_move": imp.next_move.value,
                        "rationale": imp.rationale,
                        "timestamp": imp.timestamp.isoformat(),
                    }
                    for imp in timeline
                ]
                for name, timeline in self.current_session.impression_timeline.items()
            },
            "visibility_reflections": [
                {
                    "round": ref.round_number,
                    "analysis": ref.analysis,
                    "impression_summary": ref.impression_summary,
                    "timestamp": ref.timestamp.isoformat(),
                }
                for ref in self.current_session.visibility_reflections
            ],
        }
