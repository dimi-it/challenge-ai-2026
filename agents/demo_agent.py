from __future__ import annotations

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class DemoAgent(BaseAgent):
    """A simple demonstration agent that answers general-knowledge questions.

    Tracing is handled automatically by the BaseAgent.run() method.
    This class only needs to implement the core agent logic in _execute().
    """

    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(settings, tracer, model_id, temperature, max_tokens)

    def _build_system_prompt(self) -> str:
        return (
            "You are a helpful AI assistant. "
            "Answer the user's questions concisely and accurately."
        )

    def _execute(self, user_input: str) -> str:
        """Execute the agent's core logic: invoke the LLM with the user input."""
        langfuse_handler = self._tracer.create_callback_handler()

        messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=user_input),
        ]

        response = self._model.invoke(
            messages, config={"callbacks": [langfuse_handler]}
        )
        return response.content
