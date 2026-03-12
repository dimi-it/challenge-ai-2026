# ChallengeAI2026 — Demo AI Agent with Langfuse Tracing

A modular, OOP-based project that demonstrates an AI agent built with **LangChain** and traced with **Langfuse**.

## Project Structure

```
ChallengeAI2026/
├── config/
│   ├── __init__.py
│   └── settings.py            # Environment & model configuration
├── tracing/
│   ├── __init__.py
│   └── langfuse_tracer.py     # Langfuse client, session IDs, trace viewer
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base agent (extend this)
│   └── demo_agent.py          # Demo agent implementation
├── main.py                    # Entry-point
├── .env.example               # Template for environment variables
├── requirements.txt
└── README.md
```

## Quick Start

1. **Create a virtual environment**

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux / macOS
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in your keys:

   ```bash
   cp .env.example .env
   ```

   **Provider Configuration:**
   
   Set `PROVIDER` to either `openrouter` or `openai`:
   
   - **OpenRouter** (default): Requires `OPENROUTER_API_KEY`
   - **OpenAI**: Requires `OPENAI_API_KEY`
   
   Example for OpenRouter:
   ```env
   PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
   
   Example for OpenAI:
   ```env
   PROVIDER=openai
   OPENAI_API_KEY=sk-proj-...
   ```

4. **Run the demo**

   ```bash
   python main.py
   ```

## Adding a New Agent

1. Create a new file under `agents/`, e.g. `agents/my_agent.py`.
2. Subclass `BaseAgent` and implement `_build_system_prompt()` and `run()`.
3. Decorate `run()` with `@observe()` and follow the tracing pattern in `DemoAgent`.
4. Export your class from `agents/__init__.py`.

## Key Concepts

- **Session ID** — Every run generates a unique `{TEAM_NAME}-{ULID}` session ID. All LLM calls within a session are grouped under this ID in Langfuse.
- **`@observe()` + `CallbackHandler()`** — The recommended Langfuse integration pattern for LangChain.
- **`langfuse_client.flush()`** — Always call after your agent runs to ensure traces are sent.
