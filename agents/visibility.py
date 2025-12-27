"""Visibility agent for meta-analysis of impression formation."""
from typing import List, Dict
from langchain_core.language_models import BaseChatModel
from models.schemas import ImpressionState, Message, VisibilityReflection


class VisibilityAgent:
    """
    Meta-observer agent that reflects on impression formation dynamics.

    Has privileged access to:
    - Public conversation history
    - Private impression states of all supervisors
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_reflection(
        self,
        conversation_history: List[Message],
        current_impressions: Dict[str, ImpressionState],
        impression_timeline: Dict[str, List[ImpressionState]],
        round_number: int,
    ) -> VisibilityReflection:
        """
        Generate meta-analysis of impression formation dynamics.

        Args:
            conversation_history: Full public conversation
            current_impressions: Current impression state for each supervisor
            impression_timeline: Historical impression evolution
            round_number: Current round number
        """
        prompt = self._build_reflection_prompt(
            conversation_history,
            current_impressions,
            impression_timeline,
            round_number,
        )

        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.ainvoke(messages)

        # Create impression summary
        impression_summary = {
            name: impression.stance.value
            for name, impression in current_impressions.items()
        }

        return VisibilityReflection(
            round_number=round_number,
            analysis=response.content,
            impression_summary=impression_summary,
        )

    def _build_reflection_prompt(
        self,
        conversation_history: List[Message],
        current_impressions: Dict[str, ImpressionState],
        impression_timeline: Dict[str, List[ImpressionState]],
        round_number: int,
    ) -> str:
        """Build prompt for visibility reflection."""
        # Summarize conversation
        recent_messages = conversation_history[-10:]  # Last 10 messages
        conversation_summary = "\n".join([
            f"[Round {msg.round_number}] {msg.speaker}: {msg.content[:200]}..."
            for msg in recent_messages
        ])

        # Summarize current impressions
        current_summary = []
        for name, impression in current_impressions.items():
            concerns_str = ", ".join(impression.concerns[:3]) if impression.concerns else "none"
            current_summary.append(
                f"- {name}: {impression.stance.value} (confidence: {impression.confidence.value}) "
                f"| Concerns: {concerns_str}"
            )
        current_impressions_text = "\n".join(current_summary)

        # Analyze impression evolution
        evolution_summary = []
        for name, timeline in impression_timeline.items():
            if len(timeline) > 1:
                first = timeline[0]
                latest = timeline[-1]
                if first.stance != latest.stance:
                    evolution_summary.append(
                        f"- {name}: Changed from {first.stance.value} → {latest.stance.value}"
                    )
                elif len(timeline) >= 3:
                    # Check confidence changes
                    if timeline[-3].confidence != latest.confidence:
                        evolution_summary.append(
                            f"- {name}: Confidence shifted ({timeline[-3].confidence.value} → {latest.confidence.value})"
                        )
        evolution_text = "\n".join(evolution_summary) if evolution_summary else "- No major shifts detected"

        prompt = f"""You are a meta-observer analyzing impression formation dynamics in a PhD supervision meeting.

You have privileged access to BOTH:
1. The public conversation between researcher and supervisors
2. The supervisors' PRIVATE impression states (which the researcher cannot see)

RECENT CONVERSATION:
{conversation_summary}

CURRENT PRIVATE IMPRESSIONS (Round {round_number}):
{current_impressions_text}

IMPRESSION EVOLUTION:
{evolution_text}

TASK: Provide a BRIEF, analytical reflection on impression formation dynamics.

Focus on:
1. How each supervisor's impression is currently evolving (or staying static)
2. What specific evidence seems to shift (or not shift) their views
3. Why certain supervisors resist changing perspective
4. Asymmetries in how different supervisors interpret the same researcher statements

Use PROVISIONAL, NUANCED language:
- "seems to," "appears," "likely," "suggests"
- Focus on PROCESS of impression formation, not evaluation of research quality
- Keep it concise (3-5 bullet points max)
- Use quantitative summaries where possible

CRITICAL: This is meta-analysis of social dynamics, not feedback to the researcher."""

        return prompt
