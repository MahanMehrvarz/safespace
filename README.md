# PractAI: AI-Mediated Supervision Meeting Simulator

A research prototype investigating how AI systems mediate visibility, recognition, and impression formation in professional collaborative contexts.

## Overview

PractAI simulates PhD supervision meetings where a researcher presents their work to multiple AI supervisor agents, each with distinct personalities, biases, and evaluation criteria. The system tracks private impression formation dynamics and provides meta-visibility through a dedicated analysis agent.

### Research Goals

- Investigate how workplace visibility is formed and negotiated through AI mediation
- Study impression formation dynamics across multiple evaluators
- Explore coordination challenges when AI systems reshape what is surfaced and seen
- Generate insights about multi-agent collaboration and dynamic workspaces

## Architecture

### Core Components

1. **Supervisor Agents** (3 distinct personalities)
   - **Himanshu**: HCI Methodologist - Direct, terse, focused on empirical rigor
   - **Ben**: Governance Scholar - Measured, policy-oriented, focused on accountability
   - **Dave**: Design Researcher - Warm, poetic, focused on lived experience

2. **Visibility Agent**: Meta-observer that analyzes impression formation dynamics

3. **Memory Isolation**: Each supervisor maintains separate context to prevent personality homogenization

4. **Impression Tracking**: Private states (stance, concerns, confidence) tracked separately from public responses

### Tech Stack

- **Backend**: Python, FastAPI, LangChain + LangGraph
- **Frontend**: HTML/CSS/JavaScript
- **LLM Support**: OpenAI, Anthropic, Google Gemini, Ollama
- **State Management**: LangGraph with checkpointing

## Installation

### Prerequisites

- Python 3.10+
- API key for your chosen LLM provider (or Ollama running locally)

### Setup

1. Clone/navigate to the project directory:
```bash
cd /root/practai
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

### Environment Configuration

Edit `.env` file:

```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # Options: openai, anthropic, google, ollama

# Add corresponding API key
OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# GOOGLE_API_KEY=your_key_here

# Meeting parameters
CROSS_TALK_PROBABILITY=0.3
VISIBILITY_CHECKPOINT_INTERVAL=3
```

## Usage

### Starting the Server

```bash
cd /root/practai
source venv/bin/activate
python api/main.py
```

The server starts at `http://localhost:8000`

### Using the Web Interface

1. Open browser to `http://localhost:8000`
2. Click "Start Supervision Meeting"
3. Present your research idea or proposal
4. Receive distinct responses from each supervisor
5. Continue the conversation across multiple rounds
6. Visibility reflections appear every N rounds (configurable)
7. Export session data for analysis

### API Endpoints

- `POST /api/session/start` - Start new session
- `POST /api/session/input` - Submit researcher input
- `GET /api/session/export` - Export session data
- `POST /api/session/end` - End current session
- `GET /api/health` - Health check

## Configuration

### Supervisor Personalities

Edit `config/supervisors.yaml` to modify or add supervisor personalities:

```yaml
supervisors:
  - name: SupervisorName
    role: Their academic role
    initial_stance: supportive|skeptical|unclear
    initial_confidence: low|medium|high
    personality:
      communication_style: |
        Description of how they speak
      typical_phrases:
        - "Phrase they would say"
      forbidden_phrases:
        - "Phrase they would NEVER say"
      focus_areas:
        - What they care about
```

### LLM Provider

Switch providers by changing `LLM_PROVIDER` in `.env`:

- `openai` - GPT-4, GPT-3.5
- `anthropic` - Claude 3.5 Sonnet, Claude 3 Opus
- `google` - Gemini 1.5 Pro
- `ollama` - Local models (llama3.1, mistral, etc.)

## Key Features

### Memory Isolation

Each supervisor maintains separate context:
- Only sees their own previous responses
- Receives colleague responses ONLY if cross-talk triggered (30% probability)
- Prevents personality homogenization

### Impression Tracking

Private impression states track:
- **Stance**: supportive | skeptical | unclear
- **Concerns**: List of specific concerns
- **Confidence**: low | medium | high
- **Next Move**: question | challenge | encourage
- **Rationale**: Why they hold this impression

### Visibility Reflections

Meta-analysis provided at checkpoints:
- How impressions are evolving
- What evidence shifts (or doesn't shift) views
- Why supervisors resist changing perspective
- Asymmetries across evaluators

## Data Export

Session data exports as JSON:

```json
{
  "session_id": "abc123",
  "total_rounds": 5,
  "conversation": [...],
  "impression_timeline": {
    "Himanshu": [...],
    "Ben": [...],
    "Dave": [...]
  },
  "visibility_reflections": [...]
}
```

## Research Applications

### Designed For

- Doctoral research on AI-mediated collaboration
- Studies of visibility ecosystems
- Research Through Design (RtD) methodology
- Speculative design research

### Data Analysis

Exported sessions enable analysis of:
- Impression formation dynamics
- Personality consistency metrics
- Cross-talk influence patterns
- Visibility labor and coordination work

## Troubleshooting

### Supervisors sound too similar

- Check `CROSS_TALK_PROBABILITY` - lower it to reduce context sharing
- Review supervisor personality configurations in `config/supervisors.yaml`
- Ensure distinct `forbidden_phrases` are specified

### Impression extraction fails

- Check LLM output in logs
- May need to adjust temperature (lower = more structured)
- Fallback impressions used when extraction fails

### API errors

- Verify API keys in `.env`
- Check LLM provider is accessible
- Review logs for specific error messages

## Project Structure

```
practai/
├── agents/              # Agent implementations
│   ├── supervisor.py    # Individual supervisor agents
│   ├── visibility.py    # Visibility meta-observer
│   └── meeting.py       # Meeting orchestration
├── api/                 # FastAPI backend
│   └── main.py
├── config/              # Configuration files
│   ├── supervisors.yaml # Supervisor personalities
│   ├── loader.py        # Config loader
│   └── llm_provider.py  # LLM provider setup
├── frontend/            # Web interface
│   └── index.html
├── models/              # Data models
│   └── schemas.py       # Pydantic models
├── storage/             # Session data (created at runtime)
├── requirements.txt     # Python dependencies
└── .env                 # Environment configuration
```

## Contributing

This is a research prototype. Suggestions and improvements welcome!

## License

Research prototype - contact author for usage permissions.

## Citation

If you use this prototype in your research, please cite:

```
PractAI: AI-Mediated Supervision Meeting Simulator
Research prototype for investigating visibility and impression formation
in AI-mediated professional collaboration
```

## Contact

For questions about the research context or methodology, refer to the project documentation or goals document.
