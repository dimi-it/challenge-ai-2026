from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from langchain_openai import ChatOpenAI
from langfuse import observe, propagate_attributes

from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class BaseAgent(ABC):
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

    def _create_model(self, model_id: str, temperature: float, max_tokens: int) -> ChatOpenAI:
        if self._settings.provider == "openrouter":
            return ChatOpenAI(
                api_key=self._settings.openrouter_api_key,
                base_url=self._settings.openrouter_base_url,
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if self._settings.provider == "openai":
            return ChatOpenAI(
                api_key=self._settings.openai_api_key,
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        raise ValueError(
            f"Unsupported provider: {self._settings.provider}. Must be 'openrouter' or 'openai'."
        )

    @property
    def model(self) -> ChatOpenAI:
        return self._model

    @property
    def tracer(self) -> LangfuseTracer:
        return self._tracer

    def _extract_text(self, response: Any) -> str:
        text_method = getattr(response, "text", None)
        if callable(text_method):
            text_value = text_method()
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip()

        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        parts.append(text_value)
                        continue
                    if item.get("type") == "text":
                        nested_text = item.get("text")
                        if isinstance(nested_text, str):
                            parts.append(nested_text)
                else:
                    text_value = getattr(item, "text", None)
                    if isinstance(text_value, str):
                        parts.append(text_value)
            return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
        if content not in (None, ""):
            return str(content).strip()
        return ""
        
    def _extract_tokens(self, response: Any) -> Dict[str, int]:
        usage = getattr(response, "response_metadata", {}).get("token_usage", {})
        if not usage:
            usage_metadata = getattr(response, "usage_metadata", {})
            if usage_metadata:
                return {
                    "prompt_tokens": usage_metadata.get("input_tokens", 0),
                    "completion_tokens": usage_metadata.get("output_tokens", 0),
                    "total_tokens": usage_metadata.get("total_tokens", 0),
                }
        return usage

    @abstractmethod
    def _build_system_prompt(self) -> str:
        ...

    @abstractmethod
    def _execute(self, user_input: str) -> Tuple[str, Dict[str, int]]:
        ...

    @observe()
    def run(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, int]]:
        with propagate_attributes(
            trace_name=f"{self.__class__.__name__}-run",
            session_id=session_id,
        ):
            return self._execute(user_input)
