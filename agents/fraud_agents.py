from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe, propagate_attributes

from agents.base_agent import BaseAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class FraudSignalAgent(BaseAgent):
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(settings, tracer, model_id, temperature or 0.1, max_tokens or 2000)

    def _build_system_prompt(self) -> str:
        return (
            "You are a fraud analyst. Review the context and output EXACTLY this format:\n"
            "RISK_SUMMARY: <short text>\n"
            "KEY_SIGNALS: <comma separated>\n"
            "RISK_LEVEL: <LOW|MED|HIGH>"
        )

    def _execute(self, user_input: str) -> Tuple[str, Dict[str, int]]:
        handler = self._tracer.create_callback_handler()
        messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=user_input),
        ]
        response = self._model.invoke(messages, config={"callbacks": [handler]})
        return self._extract_text(response), self._extract_tokens(response)

    @observe()
    def analyze(self, session_id: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        with propagate_attributes(trace_name="fraud-signal-agent", session_id=session_id):
            prompt = json.dumps(payload, ensure_ascii=False)
            return self.run(session_id, prompt)


class CommunicationAnalyzerAgent(BaseAgent):
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(settings, tracer, model_id, temperature or 0.0, max_tokens or 2000)

    def _build_system_prompt(self) -> str:
        return (
            "You are a cybersecurity expert. Analyze the following batch of messages and identify which ones "
            "are phishing, social engineering, scams, or contain suspicious urgent requests/links.\n"
            "Return EXACTLY a JSON list of indices (0-indexed) of the messages that are suspicious.\n"
            "If none are suspicious, return an empty list: []\n"
            "Example output:\n[0, 3, 4]"
        )

    def _execute(self, user_input: str) -> Tuple[str, Dict[str, int]]:
        handler = self._tracer.create_callback_handler()
        messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=user_input),
        ]
        response = self._model.invoke(messages, config={"callbacks": [handler]})
        text = self._extract_text(response)
        return text, self._extract_tokens(response)

    @observe()
    def analyze_batch(self, session_id: str, messages: List[str]) -> Tuple[List[int], Dict[str, int]]:
        with propagate_attributes(trace_name="communication-analyzer", session_id=session_id):
            payload = {str(i): msg for i, msg in enumerate(messages)}
            prompt = json.dumps(payload, ensure_ascii=False)
            response, usage = self.run(session_id, prompt)
            try:
                start = response.find("[")
                end = response.rfind("]") + 1
                if start != -1 and end != 0:
                    suspicious_indices = json.loads(response[start:end])
                    if isinstance(suspicious_indices, list):
                        return [int(i) for i in suspicious_indices], usage
            except Exception:
                pass
            return [], usage

class FraudDecisionAgent(BaseAgent):
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        super().__init__(settings, tracer, model_id, temperature or 0.0, max_tokens or 2500)

    def _build_system_prompt(self) -> str:
        return (
            "You are an elite fraud detection AI at Reply Mirror. "
            "Your task is to analyze a batch of candidate transactions for a user and flag the fraudulent ones.\n"
            "You will be given:\n"
            "- user_profile: Age, salary, and personal description. Pay attention if they are vulnerable to phishing or social engineering.\n"
            "- candidate_transactions: Transactions to evaluate. Each has an amount, type, location, and pre-calculated heuristic signals.\n"
            "- recent_locations: GPS pings of the user.\n"
            "- recent_communications: Recent SMS and Emails.\n\n"
            "CRITICAL FRAUD PATTERNS:\n"
            "1. Phishing / Social Engineering: Check 'recent_communications' for urgent requests (OTP, passwords, suspended accounts, verification links, suspicious investments). If a large transaction follows such messages, it is highly likely fraud.\n"
            "2. Location Mismatch: For in-person payments or withdrawals, compare the transaction 'location' against the user's 'recent_locations' and residence. Large physical distances mean fraud.\n"
            "3. Stolen Devices/Accounts: Sudden spikes in e-commerce or transfers at strange hours (e.g. 2 AM - 5 AM), especially if breaking the historical max amount.\n\n"
            "Only flag transactions you are highly confident are fraud to minimize false positives.\n"
            "Return EXACTLY this format and nothing else:\n"
            "FLAGGED_TRANSACTION_IDS:\n"
            "- <id1>\n"
            "- <id2>\n"
            "If none are fraudulent, return:\n"
            "FLAGGED_TRANSACTION_IDS:\n"
            "- NONE\n\n"
            "Example output:\n"
            "FLAGGED_TRANSACTION_IDS:\n"
            "- bcaaa9df-7f70-4a53-b9e8-f218e710c6a8"
        )

    def _execute(self, user_input: str) -> Tuple[str, Dict[str, int]]:
        handler = self._tracer.create_callback_handler()
        messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=user_input),
        ]
        response = self._model.invoke(messages, config={"callbacks": [handler]})
        text = self._extract_text(response)
        if text:
            return text, self._extract_tokens(response)
            
        print(f"DEBUG: Empty response. Retrying without system prompt.")
        # Sometimes models don't like SystemMessage, we can fallback to HumanMessage only
        fallback_messages = [
            HumanMessage(content=self._build_system_prompt() + "\n\nContext:\n" + user_input)
        ]
        retry_response = self._model.invoke(fallback_messages, config={"callbacks": [handler]})
        return self._extract_text(retry_response), self._extract_tokens(retry_response)

    @observe()
    def decide(self, session_id: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        with propagate_attributes(trace_name="fraud-decision-agent", session_id=session_id):
            prompt = json.dumps(payload, ensure_ascii=False)
            return self.run(session_id, prompt)

    @observe()
    def decide_user_batch(self, session_id: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        with propagate_attributes(trace_name="fraud-user-batch-agent", session_id=session_id):
            prompt = json.dumps(payload, ensure_ascii=False)
            return self.run(session_id, prompt)
