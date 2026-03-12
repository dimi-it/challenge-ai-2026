from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langfuse import observe, propagate_attributes

from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class BaseAgent(ABC):
    """Abstract base class for all AI agents.

    Subclasses must implement ``_build_system_prompt`` and ``run``.
    The base class provides model creation and Langfuse-traced invocation.
    """

    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        self._settings = settings
        self._tracer = tracer
        self._model = self._create_model(
            model_id or settings.default_model_id,
            temperature if temperature is not None else settings.default_temperature,
            max_tokens or settings.default_max_tokens,
        )

    def _create_model(
        self, model_id: str, temperature: float, max_tokens: int
    ) -> ChatOpenAI:
        """Instantiate a LangChain ChatOpenAI model for the configured provider."""
        if self._settings.provider == "openrouter":
            return ChatOpenAI(
                api_key=self._settings.openrouter_api_key,
                base_url=self._settings.openrouter_base_url,
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif self._settings.provider == "openai":
            return ChatOpenAI(
                api_key=self._settings.openai_api_key,
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(
                f"Unsupported provider: {self._settings.provider}. "
                "Must be 'openrouter' or 'openai'."
            )

    @property
    def model(self) -> ChatOpenAI:
        return self._model

    @property
    def tracer(self) -> LangfuseTracer:
        return self._tracer

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Return the system prompt that defines this agent's personality/role."""
        ...

    @abstractmethod
    def _execute(self, user_input: str) -> str:
        """Execute the agent's core logic on *user_input*.

        Subclasses implement this method with their specific agent behavior.
        Tracing is handled automatically by the base class run() method.
        """
        ...

    @observe()
    def run(self, session_id: str, user_input: str) -> str:
        """Execute the agent on *user_input* under the given *session_id*.

        This method handles Langfuse tracing automatically. Subclasses should
        implement _execute() instead of overriding this method.
        """
        with propagate_attributes(
            trace_name=f"{self.__class__.__name__}-run",
            session_id=session_id,
        ):
            return self._execute(user_input)
