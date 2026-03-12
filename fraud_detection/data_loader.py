from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dateutil import parser


@dataclass
class Communication:
    text: str
    timestamp: Optional[datetime]
    type: str

@dataclass
class DatasetBundle:
    dataset_name: str
    root: Path
    transactions: List[Dict[str, Any]]
    users: Dict[str, Dict[str, Any]]
    locations_by_user: Dict[str, List[Dict[str, Any]]]
    conversations_by_user: Dict[str, List[Communication]]
    messages_by_user: Dict[str, List[Communication]]


def discover_dataset_bundle(project_root: Path, dataset_name: Optional[str] = None) -> DatasetBundle:
    search_roots = _candidate_roots(project_root, dataset_name)
    best_root: Optional[Path] = None
    transaction_file: Optional[Path] = None

    for root in search_roots:
        candidate = _find_transactions_file(root)
        if candidate is not None:
            best_root = candidate.parent
            transaction_file = candidate
            break

    if best_root is None or transaction_file is None:
        raise FileNotFoundError(
            "Could not find a transactions dataset. Add a folder containing Transactions.csv or transactions.csv."
        )

    transactions = _load_table(transaction_file)
    users = _load_users(_find_named_file(best_root, {"users"}), transactions)
    locations_by_user = _group_by_user(_load_table(_find_named_file(best_root, {"locations"})))
    conversations_by_user = _extract_text_threads(
        _load_table(_find_named_file(best_root, {"conversations", "sms"})),
        users,
        comm_type="sms"
    )
    messages_by_user = _extract_text_threads(
        _load_table(_find_named_file(best_root, {"messages", "mails", "mail"})),
        users,
        comm_type="mail"
    )

    return DatasetBundle(
        dataset_name=best_root.name,
        root=best_root,
        transactions=transactions,
        users=users,
        locations_by_user=locations_by_user,
        conversations_by_user=conversations_by_user,
        messages_by_user=messages_by_user,
    )


def _candidate_roots(project_root: Path, dataset_name: Optional[str]) -> List[Path]:
    roots: List[Path] = []
    if dataset_name:
        roots.append(project_root / dataset_name)
        roots.append(project_root.parent / dataset_name)
        roots.append(project_root / "training datasets" / dataset_name)
        roots.append(project_root.parent / "training datasets" / dataset_name)
    roots.append(project_root)
    roots.append(project_root.parent)
    roots.append(project_root / "training datasets")

    expanded: List[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for candidate in [root, *[child for child in root.iterdir() if child.is_dir()]]:
            resolved = candidate.resolve()
            if resolved not in seen:
                expanded.append(candidate)
                seen.add(resolved)
    return expanded


def _find_transactions_file(root: Path) -> Optional[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        normalized = _normalize_name(path.stem)
        if "__macosx" in {part.lower() for part in path.parts}:
            continue
        if normalized == "transactions" and path.suffix.lower() in {".csv", ".json"}:
            return path
    return None


def _find_named_file(root: Path, names: set[str]) -> Optional[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__macosx" in {part.lower() for part in path.parts}:
            continue
        normalized = _normalize_name(path.stem)
        if normalized in names and path.suffix.lower() in {".csv", ".json", ".txt"}:
            return path
    return None


def _load_users(path: Optional[Path], transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    rows = _load_table(path)
    users: Dict[str, Dict[str, Any]] = {}
    iban_to_biotag = _build_iban_to_biotag_map(transactions)

    for row in rows:
        user_record = dict(row)
        iban = _first_present(user_record, ["iban"])
        biotag = iban_to_biotag.get(str(iban), "") if iban else ""
        full_name = _build_full_name(user_record)
        email = _build_email(user_record)

        user_record["user_id"] = biotag or str(iban or full_name)
        user_record["biotag"] = biotag
        user_record["full_name"] = full_name
        user_record["email"] = email

        for candidate in [user_record["user_id"], biotag, iban, email, full_name]:
            if candidate:
                users[str(candidate)] = user_record
    return users


def _group_by_user(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        user_id = _first_present(row, ["user_id", "userid", "user id", "bio_tag", "biotag", "citizenid", "citizen_id", "sender_id", "sender id"])
        if user_id is None:
            continue
        grouped.setdefault(str(user_id), []).append(row)
    return grouped


def _extract_text_threads(rows: List[Dict[str, Any]], users: Dict[str, Dict[str, Any]], comm_type: str = "unknown") -> Dict[str, List[Communication]]:
    grouped: Dict[str, List[Communication]] = {}
    matchers = _build_user_matchers(users)

    for row in rows:
        user_id = _first_present(row, ["user_id", "userid", "user id", "bio_tag", "biotag", "citizenid", "citizen_id", "sender_id", "sender id"])
        content = _first_present(row, ["sms", "mail", "message", "thread", "text", "body"])
        if not content:
            continue

        content_text = str(content)
        
        # Try to extract timestamp
        timestamp = None
        date_m = re.search(r'Date:\s*([^\n]+)', content_text)
        if date_m:
            try:
                timestamp = parser.parse(date_m.group(1))
            except Exception:
                pass

        inferred_user_ids = [str(user_id)] if user_id is not None else _infer_user_ids(content_text, matchers)
        for inferred_user_id in inferred_user_ids:
            grouped.setdefault(inferred_user_id, []).append(Communication(text=content_text, timestamp=timestamp, type=comm_type))

    return grouped


def _load_table(path: Optional[Path]) -> List[Dict[str, Any]]:
    if path is None or not path.exists():
        return []

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [_normalize_row(row) for row in csv.DictReader(handle)]

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [_normalize_row(item) for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for value in payload.values():
                if isinstance(value, list):
                    return [_normalize_row(item) for item in value if isinstance(item, dict)]
        return []

    if path.suffix.lower() == ".txt":
        with path.open("r", encoding="utf-8") as handle:
            return [{"text": handle.read()}]

    return []


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {str(key).strip(): value for key, value in row.items()}


def _normalize_name(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _first_present(row: Dict[str, Any], keys: Iterable[str]) -> Any:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        if key in lowered and lowered[key] not in (None, ""):
            return lowered[key]
    return None


def _build_iban_to_biotag_map(transactions: List[Dict[str, Any]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for row in transactions:
        sender_id = _first_present(row, ["sender_id", "sender id", "Sender ID"])
        sender_iban = _first_present(row, ["sender_iban", "sender iban", "Sender IBAN"])
        recipient_id = _first_present(row, ["recipient_id", "recipient id", "Recipient ID"])
        recipient_iban = _first_present(row, ["recipient_iban", "recipient iban", "Recipient IBAN"])

        if sender_id and sender_iban:
            mapping[str(sender_iban)] = str(sender_id)
        if recipient_id and recipient_iban:
            mapping[str(recipient_iban)] = str(recipient_id)
    return mapping


def _build_full_name(user_record: Dict[str, Any]) -> str:
    first_name = str(_first_present(user_record, ["first_name", "firstname", "first name"]) or "").strip()
    last_name = str(_first_present(user_record, ["last_name", "lastname", "last name"]) or "").strip()
    return " ".join(part for part in [first_name, last_name] if part).strip()


def _build_email(user_record: Dict[str, Any]) -> str:
    first_name = str(_first_present(user_record, ["first_name", "firstname", "first name"]) or "").strip().lower()
    last_name = str(_first_present(user_record, ["last_name", "lastname", "last name"]) or "").strip().lower()
    if not first_name or not last_name:
        return ""
    return f"{first_name}.{last_name}@example.com"


def _build_user_matchers(users: Dict[str, Dict[str, Any]]) -> Dict[str, List[Tuple[str, re.Pattern[str]]]]:
    matchers: Dict[str, List[Tuple[str, re.Pattern[str]]]] = {}
    seen_user_ids: set[str] = set()

    for user_record in users.values():
        user_id = str(user_record.get("user_id") or "")
        if not user_id or user_id in seen_user_ids:
            continue
        seen_user_ids.add(user_id)

        patterns: List[Tuple[str, re.Pattern[str]]] = []
        full_name = str(user_record.get("full_name") or "").strip()
        first_name = str(_first_present(user_record, ["first_name", "firstname", "first name"]) or "").strip()
        email = str(user_record.get("email") or "").strip()

        for token in [full_name, first_name, email]:
            if not token:
                continue
            patterns.append((token, re.compile(re.escape(token), re.IGNORECASE)))

        matchers[user_id] = patterns

    return matchers


def _infer_user_ids(content: str, matchers: Dict[str, List[Tuple[str, re.Pattern[str]]]]) -> List[str]:
    matches: List[str] = []
    for user_id, user_patterns in matchers.items():
        if any(pattern.search(content) for _, pattern in user_patterns):
            matches.append(user_id)
    return matches
