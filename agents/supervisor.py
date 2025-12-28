"""Supervisor agent implementation with memory isolation."""
import json
import re
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from models.schemas import (
    SupervisorConfig,
    ImpressionState,
    SupervisorResponse,
    Stance,
    Confidence,
    NextMove,
    Message,
)


class SupervisorAgent:
    """
    Individual supervisor agent with isolated memory and personality.

    Critical for preventing personality homogenization:
    - Each supervisor maintains separate conversation history
    - Only sees colleague responses if cross-talk is triggered
    - Strong personality enforcement in prompts
    """

    def __init__(self, config: SupervisorConfig, llm: BaseChatModel):
        self.config = config
        self.llm = llm
        self.name = config.name
        self.current_impression: Optional[ImpressionState] = None
        self.my_previous_responses: List[str] = []

    def _build_personality_prompt(self) -> str:
        """Build strong personality enforcement prompt."""
        personality = self.config.personality

        # Extract typical and forbidden phrases
        typical_phrases = personality.get('typical_phrases', [])
        forbidden_phrases = personality.get('forbidden_phrases', [])

        prompt = f"""You are {self.config.name}, a {self.config.role}.

COMMUNICATION STYLE:
{personality.get('communication_style', '')}

YOUR TYPICAL LANGUAGE PATTERNS (use these):
{chr(10).join(f'- "{phrase}"' for phrase in typical_phrases)}

ABSOLUTELY FORBIDDEN LANGUAGE (NEVER use these):
{chr(10).join(f'- "{phrase}"' for phrase in forbidden_phrases)}

YOUR FOCUS AREAS:
{chr(10).join(f'- {area}' for area in self.config.focus_areas)}

WHAT CONVINCES YOU:
{chr(10).join(f'- {item}' for item in self.config.what_convinces)}

CRITICAL PERSONALITY RULES:
1. You are NOT like the other supervisors. Maintain YOUR distinct voice.
2. Do NOT copy language patterns from colleagues (Dave, Ben, Himanshu).
3. Stay true to YOUR communication style even when you hear others speak differently.
4. If you are {self.config.name}, you speak ONLY in your own voice.

FORBIDDEN: Do not use phrases, metaphors, or tone from other supervisors."""

        return prompt

    def _build_impression_extraction_prompt(self) -> str:
        """Prompt for extracting structured impression."""
        return """
After your response, you MUST include a JSON block with your private impression:

<IMPRESSION>
{
  "stance": "supportive|skeptical|unclear",
  "concerns": ["concern1", "concern2"],
  "confidence": "low|medium|high",
  "next_move": "question|challenge|encourage",
  "rationale": "brief explanation of your current assessment"
}
</IMPRESSION>

The impression is private - the researcher won't see it."""

    async def respond(
        self,
        researcher_input: str,
        round_number: int,
        colleague_responses: Optional[List[tuple[str, str]]] = None,
        conversation_history: Optional[List] = None,
    ) -> SupervisorResponse:
        """
        Generate response to researcher input.

        Args:
            researcher_input: What the researcher said THIS round
            round_number: Current round number
            colleague_responses: Optional list of (supervisor_name, response) tuples
                               Only provided if cross-talk is triggered
            conversation_history: Full conversation history for context
        """
        # Build context with memory isolation
        context_parts = []

        # Add previous impression for concern tracking
        if self.current_impression and round_number > 1:
            context_parts.append("YOUR PREVIOUS IMPRESSION:")
            context_parts.append(f"Stance: {self.current_impression.stance.value}")
            context_parts.append(f"Confidence: {self.current_impression.confidence.value}")
            if self.current_impression.concerns:
                context_parts.append(f"Previous Concerns:")
                for concern in self.current_impression.concerns:
                    context_parts.append(f"  - {concern}")
            context_parts.append("")

        # Add conversation history (researcher's previous statements + your responses)
        if conversation_history and round_number > 1:
            context_parts.append("PREVIOUS CONVERSATION:")
            for msg in conversation_history[-(round_number * 4):]:  # Last few rounds
                if msg.speaker == "Researcher":
                    context_parts.append(f"[Round {msg.round_number}] Researcher: {msg.content[:300]}...")
                elif msg.speaker == self.name:
                    context_parts.append(f"[Round {msg.round_number}] You said: {msg.content[:200]}...")
            context_parts.append("")

        # Add researcher's current input
        context_parts.append(f"RESEARCHER'S CURRENT STATEMENT (Round {round_number}):\n{researcher_input}")

        # Add colleague responses ONLY if cross-talk triggered
        references = []
        if colleague_responses:
            context_parts.append("\nCOLLEAGUE RESPONSES THIS ROUND:")
            for col_name, col_response in colleague_responses:
                context_parts.append(f"- {col_name}: {col_response[:300]}...")
                references.append(col_name)

        context = "\n".join(context_parts)

        # Build full prompt
        personality_prompt = self._build_personality_prompt()
        impression_prompt = self._build_impression_extraction_prompt()

        concern_resolution_instructions = ""
        if round_number > 1 and self.current_impression and self.current_impression.concerns:
            concern_resolution_instructions = f"""
CRITICAL: CONCERN RESOLUTION TRACKING
You had {len(self.current_impression.concerns)} concern(s) in the previous round.

For EACH previous concern, evaluate:
1. Has the researcher's new input DIRECTLY addressed this concern?
2. If YES → DO NOT include it in your new concerns list (it's resolved!)
3. If NO → Include it again, BUT make it more specific based on what they said
4. New concerns can emerge based on their latest input

IMPORTANT: Only list UNRESOLVED or NEW concerns in your impression. Resolved concerns should disappear.

If a concern is addressed:
- Your confidence should INCREASE
- Your stance may shift more positive
- Acknowledge the progress in your response (briefly)
"""

        full_prompt = f"""{personality_prompt}

{context}

CRITICAL INSTRUCTIONS FOR THIS ROUND:

1. **BUILD ON THE CONVERSATION**: This is Round {round_number}. You have already spoken in previous rounds.
   - DO NOT repeat the same concerns verbatim
   - Reference what the researcher JUST said in their latest statement
   - Either acknowledge progress OR explain why your concerns remain
   - If they addressed something, say so. If they didn't, point that out specifically.

2. **RESPOND TO THEIR LATEST INPUT**: The researcher just said something new. React to THAT.
   - Quote or reference specific parts of what they just said
   - Build on it, critique it, or ask follow-up questions
   - Don't give the same generic response you gave in Round 1

3. **EVOLVE YOUR RESPONSE**: Your concerns should either:
   - Get more specific (if they're not addressing them)
   - Shift focus (if they partially addressed some)
   - Decrease (if they're making progress)

4. **AVOID VERBATIM REPETITION**:
   - Don't use the exact same phrases as previous rounds
   - Don't ask the exact same questions again
   - Vary your language while staying true to your personality

5. **MAINTAIN YOUR VOICE**:
   - Speak ONLY as {self.config.name} (not like {', '.join([n for n in ['Dave', 'Ben', 'Himanshu'] if n != self.name])})
   - Use YOUR typical language patterns
   - Focus on YOUR areas of concern
   - NEVER use your forbidden phrases

{concern_resolution_instructions}

Now respond to the researcher's LATEST statement. Make it clear you're building on an ongoing conversation, not starting fresh.

{impression_prompt}"""

        # Get LLM response
        messages = [{"role": "user", "content": full_prompt}]
        response = await self.llm.ainvoke(messages)
        full_response = response.content

        # Extract public response and impression
        public_response, impression = self._extract_response_and_impression(full_response)

        # Store this response in own memory
        self.my_previous_responses.append(public_response)
        self.current_impression = impression

        return SupervisorResponse(
            supervisor_name=self.name,
            public_response=public_response,
            impression=impression,
            references_colleagues=references,
            round_number=round_number,
        )

    def _extract_response_and_impression(self, full_response: str) -> tuple[str, ImpressionState]:
        """Extract public response and private impression from LLM output."""
        # Try to extract JSON from <IMPRESSION> tags
        impression_match = re.search(
            r'<IMPRESSION>\s*(\{.*?\})\s*</IMPRESSION>',
            full_response,
            re.DOTALL
        )

        if impression_match:
            try:
                impression_json = json.loads(impression_match.group(1))
                impression = ImpressionState(
                    stance=Stance(impression_json['stance']),
                    concerns=impression_json.get('concerns', []),
                    confidence=Confidence(impression_json['confidence']),
                    next_move=NextMove(impression_json['next_move']),
                    rationale=impression_json.get('rationale', ''),
                )
                # Remove impression block from public response
                public_response = full_response[:impression_match.start()].strip()
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Fallback if extraction fails
                impression = self._create_fallback_impression()
                public_response = full_response.replace(impression_match.group(0), '').strip()
        else:
            # No impression found - use fallback
            impression = self._create_fallback_impression()
            public_response = full_response

        return public_response, impression

    def _create_fallback_impression(self) -> ImpressionState:
        """Create default impression if extraction fails."""
        return ImpressionState(
            stance=self.config.initial_stance,
            confidence=self.config.initial_confidence,
            concerns=["Unable to extract impression"],
            next_move=NextMove.QUESTION,
            rationale="Impression extraction failed, using default",
        )

    def get_current_impression(self) -> ImpressionState:
        """Get the most recent impression state."""
        if self.current_impression is None:
            return self._create_fallback_impression()
        return self.current_impression
