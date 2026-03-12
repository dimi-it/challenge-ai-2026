"""
ChallengeAI2026 — Reply Mirror Fraud Detection System
======================================================
Entry-point for a multi-agent fraud detection pipeline.

Usage:
    python main.py [dataset_name]
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from langfuse import observe, propagate_attributes

from agents import CommunicationAnalyzerAgent, FraudDecisionAgent, FraudSignalAgent
from config.settings import Settings
from fraud_detection.data_loader import discover_dataset_bundle
from fraud_detection.risk_engine import FraudContextBuilder, score_transaction
from tracing.langfuse_tracer import LangfuseTracer


@observe()
def run_session(
    session_id: str,
    transactions: List[Dict[str, Any]],
    context_builder: FraudContextBuilder,
    signal_agent: FraudSignalAgent,
    comm_analyzer: CommunicationAnalyzerAgent,
    decision_agent: FraudDecisionAgent,
) -> Tuple[List[str], Dict[str, int]]:
    flagged_transaction_ids: List[str] = []
    total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _add_tokens(usage: Dict[str, int]):
        total_tokens["prompt_tokens"] += usage.get("prompt_tokens", 0)
        total_tokens["completion_tokens"] += usage.get("completion_tokens", 0)
        total_tokens["total_tokens"] += usage.get("total_tokens", 0)

    with propagate_attributes(
        trace_name="reply-mirror-fraud-session",
        session_id=session_id,
    ):
        transactions_by_user = _group_transactions_by_sender(transactions)
        user_ids = list(transactions_by_user.keys())

        for user_index, user_id in enumerate(user_ids):
            user_transactions = transactions_by_user[user_id]
            print(f"[{user_index + 1}/{len(user_ids)}] Start user {user_id} with {len(user_transactions)} transactions")
            scored_transactions: List[Dict[str, Any]] = []

            for transaction in user_transactions:
                transaction_index = transactions.index(transaction)
                transaction_id = _transaction_id(transaction, transaction_index)
                context = context_builder.build(transaction, transaction_index)
                heuristic_result = score_transaction(context)
                scored_transactions.append(
                    {
                        "transaction_id": transaction_id,
                        "transaction": transaction,
                        "heuristics": heuristic_result,
                        "recipient_profile": context.recipient_profile,
                        "sender_profile": context.sender_profile,
                    }
                )

            scored_transactions.sort(key=lambda item: item["heuristics"]["total_score"], reverse=True)
            
            user_flagged = [t["transaction_id"] for t in scored_transactions if t["heuristics"]["decision_hint"] == "flag"]

            candidate_transactions = [t for t in scored_transactions if t["heuristics"]["decision_hint"] == "review"]
            candidate_transactions = candidate_transactions[: min(5, len(candidate_transactions))]
            
            if not candidate_transactions:
                if user_flagged:
                    print(f"[{user_index + 1}/{len(user_ids)}] Auto-flagged {len(user_flagged)} transactions for {user_id}")
                    flagged_transaction_ids.extend(user_flagged)
                else:
                    print(f"[{user_index + 1}/{len(user_ids)}] Skipping user {user_id}: no suspicious transactions")
                continue

            representative = user_transactions[0]
            representative_index = transactions.index(representative)
            representative_context = context_builder.build(representative, representative_index)

            # Prune payload size to optimize tokens and efficiency
            compact_candidates = []
            
            for item in candidate_transactions:
                compact_candidates.append({
                    "transaction_id": item["transaction_id"],
                    "amount": item["transaction"].get("amount") or item["transaction"].get("Amount"),
                    "type": item["transaction"].get("transaction_type") or item["transaction"].get("Transaction Type"),
                    "method": item["transaction"].get("payment_method") or item["transaction"].get("Payment Method"),
                    "location": item["transaction"].get("location") or item["transaction"].get("Location"),
                    "heuristics_score": item["heuristics"]["total_score"],
                    "signals": [s["name"] for s in item["heuristics"]["signals"]],
                })
                
            # Cooperative Multi-Agent Step 1: Communication Analyzer (Adaptive Phishing Detection)
            recent_comms = []
            for comm in (representative_context.sender_conversations + representative_context.sender_messages)[-15:]:
                recent_comms.append(comm.text[:300]) # truncate long emails
                
            suspicious_comm_flags = []
            if recent_comms:
                print(f"[{user_index + 1}/{len(user_ids)}] Calling communication analyzer for {len(recent_comms)} messages")
                suspicious_indices, usage = comm_analyzer.analyze_batch(session_id, recent_comms)
                _add_tokens(usage)
                for idx in suspicious_indices:
                    if 0 <= idx < len(recent_comms):
                        suspicious_comm_flags.append(recent_comms[idx])

            # Cooperative Multi-Agent Step 2: Decision Agent
            print(f"[{user_index + 1}/{len(user_ids)}] Calling decision agent for user {user_id}")
            
            # Format comms and locations
            recent_locs = representative_context.sender_locations[-3:] if representative_context.sender_locations else []
                
            batch_decision, usage = decision_agent.decide_user_batch(
                session_id=session_id,
                payload={
                    "user_id": user_id,
                    "user_profile": {
                        "age": 2087 - (representative_context.sender_profile.get("birth_year") or 2000),
                        "description": representative_context.sender_profile.get("description", ""),
                        "salary": representative_context.sender_profile.get("salary", 0),
                    },
                    "candidate_transactions": compact_candidates,
                    "recent_locations": recent_locs,
                    "suspicious_communications": suspicious_comm_flags,
                },
            )
            _add_tokens(usage)

            print(f"[{user_index + 1}/{len(user_ids)}] Decision agent completed for user {user_id}")
            print(f"[{user_index + 1}/{len(user_ids)}] Raw batch decision for user {user_id}: {batch_decision!r}")
            llm_flagged_for_user = _parse_flagged_transaction_ids(batch_decision, {item['transaction_id'] for item in candidate_transactions})
            
            all_user_flagged = list(set(user_flagged + llm_flagged_for_user))
            print(f"[{user_index + 1}/{len(user_ids)}] User {user_id} flagged transactions: {all_user_flagged}")
            flagged_transaction_ids.extend(all_user_flagged)

    return _enforce_output_constraints(flagged_transaction_ids, transactions), total_tokens


def main() -> None:
    settings = Settings()
    settings.validate()

    tracer = LangfuseTracer(settings)
    project_root = Path(__file__).resolve().parent
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DATASET_LEVEL")

    bundle = discover_dataset_bundle(project_root=project_root, dataset_name=dataset_name)
    transactions = sorted(bundle.transactions, key=_transaction_sort_key)
    session_id = tracer.generate_session_id()

    print(f"Model configured: {settings.default_model_id}")
    print(f"Langfuse initialized (host: {settings.langfuse_host})")
    print(f"Dataset root: {bundle.root}")
    print(f"Transactions loaded: {len(transactions)}")
    print(f"Session ID: {session_id}\n")

    context_builder = FraudContextBuilder(
        transactions=transactions,
        users=bundle.users,
        locations_by_user=bundle.locations_by_user,
        conversations_by_user=bundle.conversations_by_user,
        messages_by_user=bundle.messages_by_user,
    )
    signal_agent = FraudSignalAgent(settings=settings, tracer=tracer)
    decision_agent = FraudDecisionAgent(settings=settings, tracer=tracer)
    comm_analyzer = CommunicationAnalyzerAgent(settings=settings, tracer=tracer)

    dataset_label = dataset_name or bundle.dataset_name or bundle.root.parent.name or bundle.root.name or "dataset"
    dataset_slug = _slugify(dataset_label)

    try:
        flagged_transaction_ids, token_usage = run_session(
            session_id=session_id,
            transactions=transactions,
            context_builder=context_builder,
            signal_agent=signal_agent,
            comm_analyzer=comm_analyzer,
            decision_agent=decision_agent,
        )

        output_dir = project_root / "output" / dataset_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_slug = _slugify(session_id)
        
        output_path = output_dir / f"output_{session_slug}_{run_timestamp}.txt"
        with output_path.open("w", encoding="ascii") as handle:
            for transaction_id in flagged_transaction_ids:
                handle.write(f"{transaction_id}\n")

        print(f"\nWritten {len(flagged_transaction_ids)} suspicious transaction IDs to: {output_path}")
    finally:
        if 'token_usage' in locals():
            print(f"\nToken usage for this run: {token_usage}")
        else:
            print("\nToken usage: unavailable for this run")


def _is_flagged(decision_text: str) -> bool:
    first_line = decision_text.strip().splitlines()[0].strip().upper() if decision_text.strip() else ""
    if "DECISION: FLAG" in first_line:
        return True
    if "DECISION: ALLOW" in first_line:
        return False
    print(f"Unparseable decision output, defaulting to ALLOW: {decision_text!r}")
    return False


def _parse_flagged_transaction_ids(decision_text: str, valid_ids: Set[str]) -> List[str]:
    flagged_ids: List[str] = []
    for raw_line in decision_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        candidate = line[1:].strip()
        if candidate.upper() == "NONE":
            return []
        if candidate in valid_ids:
            flagged_ids.append(candidate)
    return list(dict.fromkeys(flagged_ids))


def _enforce_output_constraints(flagged_ids: List[str], transactions: List[Dict[str, Any]]) -> List[str]:
    unique_ids = list(dict.fromkeys(flagged_ids))
    total_transactions = len(transactions)
    if total_transactions == 0:
        return []

    all_transaction_ids = [
        str(_get_value(row, ["Transaction ID", "transaction_id", "transaction id", "id"]) or f"transaction-{index}")
        for index, row in enumerate(transactions)
    ]

    if not unique_ids:
        unique_ids = [all_transaction_ids[0]]
    if len(unique_ids) >= total_transactions:
        unique_ids = all_transaction_ids[: max(1, total_transactions - 1)]
    return unique_ids


def _transaction_sort_key(row: Dict[str, Any]) -> str:
    return str(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"]) or "")


def _group_transactions_by_sender(transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for index, transaction in enumerate(transactions):
        sender_id = str(_get_value(transaction, ["Sender ID", "sender_id", "sender id"]) or f"unknown-sender-{index}")
        grouped.setdefault(sender_id, []).append(transaction)
    return grouped


def _transaction_id(transaction: Dict[str, Any], index: int) -> str:
    return str(_get_value(transaction, ["Transaction ID", "transaction_id", "transaction id", "id"]) or f"transaction-{index}")


def _slugify(value: str) -> str:
    cleaned = [character.lower() if character.isalnum() else "-" for character in str(value).strip()]
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "run"


def _get_value(row: Dict[str, Any], keys: List[str]) -> Any:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        match = lowered.get(key.lower())
        if match not in (None, ""):
            return match
    return None


if __name__ == "__main__":
    main()
