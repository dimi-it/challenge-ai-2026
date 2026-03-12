"""
ChallengeAI2026 — Demo AI Agent with Langfuse Tracing
======================================================
Entry-point that demonstrates a traced LangChain agent.

Usage:
    python main.py
"""

from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer
from agents.demo_agent import DemoAgent


def main() -> None:
    # ── Configuration ────────────────────────────────────────────────
    settings = Settings()
    settings.validate()
    print(f"Model configured: {settings.default_model_id}")

    # ── Langfuse tracer ──────────────────────────────────────────────
    tracer = LangfuseTracer(settings)
    print(f"Langfuse initialized (host: {settings.langfuse_host})")

    # ── Agent ────────────────────────────────────────────────────────
    agent = DemoAgent(settings=settings, tracer=tracer)

    # ── Generate a unique session ID (essential for the challenge) ───
    session_id = tracer.generate_session_id()
    print(f"Session ID: {session_id}\n")

    # ── Single call demo ─────────────────────────────────────────────
    print("=" * 50)
    print("SINGLE CALL DEMO")
    print("=" * 50)

    prompt = "What is the square root of 144?"
    response = agent.run(session_id, prompt)
    print(f"Input:    {prompt}")
    print(f"Response: {response}\n")

    # ── Multi-call demo (same session) ───────────────────────────────
    print("=" * 50)
    print("MULTI-CALL DEMO (same session)")
    print("=" * 50)

    questions = [
        "What is machine learning?",
        "Explain neural networks briefly.",
        "What is the difference between AI and ML?",
    ]

    for i, question in enumerate(questions, 1):
        resp = agent.run(session_id, question)
        print(f"Call {i}: {question}")
        print(f"  Response: {resp[:120]}...\n")

    # ── Flush traces to Langfuse ─────────────────────────────────────
    tracer.flush()
    print(f"All traces flushed to Langfuse under session: {session_id}")

    # ── Inspect traces ───────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("TRACE INSPECTION")
    print("=" * 50)

    info = tracer.get_trace_info(session_id)
    LangfuseTracer.print_results(info)


if __name__ == "__main__":
    main()
