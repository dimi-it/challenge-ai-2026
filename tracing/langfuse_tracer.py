from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional

import ulid
from langfuse import Langfuse, observe
from langfuse.langchain import CallbackHandler

from config.settings import Settings


class LangfuseTracer:
    """Manages Langfuse client lifecycle, session IDs, and trace inspection."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )

    @property
    def client(self) -> Langfuse:
        return self._client

    def generate_session_id(self) -> str:
        """Generate a unique session ID in the format {TEAM_NAME}-{ULID}."""
        return f"{self._settings.team_name}-{ulid.new().str}"

    def create_callback_handler(self) -> CallbackHandler:
        """Create a new Langfuse CallbackHandler attached to the current trace."""
        return CallbackHandler()

    def flush(self) -> None:
        """Flush all pending traces to the Langfuse server."""
        self._client.flush()

    # ------------------------------------------------------------------
    # Trace inspection utilities (from tutorial)
    # ------------------------------------------------------------------

    def get_trace_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch traces for a session_id and aggregate basic statistics.

        Returns a dict with:
          - counts: {model -> num_generations}
          - costs:  {model -> total_cost}
          - time:   total time across generations (seconds)
          - input:  preview of first input
          - output: preview of last output
        """
        traces: list = []
        page = 1

        while True:
            response = self._client.api.trace.list(
                session_id=session_id, limit=100, page=page
            )
            if not response.data:
                break
            traces.extend(response.data)
            if len(response.data) < 100:
                break
            page += 1

        if not traces:
            return None

        observations: list = []
        for trace in traces:
            detail = self._client.api.trace.get(trace.id)
            if detail and hasattr(detail, "observations"):
                observations.extend(detail.observations)

        if not observations:
            return None

        sorted_obs = sorted(
            observations,
            key=lambda o: (
                o.start_time
                if hasattr(o, "start_time") and o.start_time
                else datetime.min
            ),
        )

        counts: Dict[str, int] = defaultdict(int)
        costs: Dict[str, float] = defaultdict(float)
        total_time = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        for obs in observations:
            if hasattr(obs, "type") and obs.type == "GENERATION":
                model = getattr(obs, "model", "unknown") or "unknown"
                counts[model] += 1

                usage_details = getattr(obs, "usage_details", None)
                if isinstance(usage_details, dict):
                    prompt_tokens += int(usage_details.get("input", 0) or 0)
                    completion_tokens += int(usage_details.get("output", 0) or 0)
                    total_tokens += int(usage_details.get("total", 0) or 0)

                prompt_tokens += int(getattr(obs, "prompt_tokens", 0) or 0)
                completion_tokens += int(getattr(obs, "completion_tokens", 0) or 0)
                total_tokens += int(getattr(obs, "total_tokens", 0) or 0)

                if (
                    hasattr(obs, "calculated_total_cost")
                    and obs.calculated_total_cost
                ):
                    costs[model] += obs.calculated_total_cost

                if hasattr(obs, "start_time") and hasattr(obs, "end_time"):
                    if obs.start_time and obs.end_time:
                        total_time += (
                            obs.end_time - obs.start_time
                        ).total_seconds()

        first_input = ""
        if sorted_obs and hasattr(sorted_obs[0], "input"):
            inp = sorted_obs[0].input
            if inp:
                first_input = str(inp)[:100]

        last_output = ""
        if sorted_obs and hasattr(sorted_obs[-1], "output"):
            out = sorted_obs[-1].output
            if out:
                last_output = str(out)[:100]

        return {
            "counts": dict(counts),
            "costs": dict(costs),
            "time": total_time,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens or (prompt_tokens + completion_tokens),
            },
            "input": first_input,
            "output": last_output,
        }

    @staticmethod
    def print_results(info: Optional[Dict[str, Any]]) -> None:
        """Pretty-print the aggregated trace information."""
        if not info:
            print("\nNo traces found for this session_id.\n")
            return

        print("\nTrace Count by Model:")
        for model, count in info["counts"].items():
            print(f"  {model}: {count}")

        print("\nCost by Model:")
        total = 0.0
        for model, cost in info["costs"].items():
            print(f"  {model}: ${cost:.6f}")
            total += cost
        if total > 0:
            print(f"  Total: ${total:.6f}")

        tokens = info.get("tokens", {})
        if tokens:
            print("\nToken Usage:")
            print(f"  Prompt: {tokens.get('prompt', 0)}")
            print(f"  Completion: {tokens.get('completion', 0)}")
            print(f"  Total: {tokens.get('total', 0)}")

        print(f"\nTotal Time: {info['time']:.2f}s")

        if info["input"]:
            print(f"\nInitial Input:\n  {info['input']}")

        if info["output"]:
            print(f"\nFinal Output:\n  {info['output']}")

        print()
