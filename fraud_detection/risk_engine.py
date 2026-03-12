from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

from fraud_detection.data_loader import Communication

@dataclass
class FraudSignal:
    name: str
    score: float
    evidence: str

@dataclass
class TransactionContext:
    transaction: Dict[str, Any]
    sender_profile: Dict[str, Any]
    recipient_profile: Dict[str, Any]
    sender_history: List[Dict[str, Any]]
    recipient_history: List[Dict[str, Any]]
    sender_locations: List[Dict[str, Any]]
    sender_conversations: List[Communication]
    sender_messages: List[Communication]
    transaction_index: int
    global_median_salary: float
    global_median_distance: float
    global_median_velocity: float
    user_velocity_stats: Dict[str, float]
    user_location_stats: Dict[str, float]

class FraudContextBuilder:
    def __init__(self, transactions: List[Dict[str, Any]], users: Dict[str, Dict[str, Any]], locations_by_user: Dict[str, List[Dict[str, Any]]], conversations_by_user: Dict[str, List[Communication]], messages_by_user: Dict[str, List[Communication]]) -> None:
        self._transactions = transactions
        self._users = users
        self._locations_by_user = locations_by_user
        self._conversations_by_user = conversations_by_user
        self._messages_by_user = messages_by_user
        self._history_by_sender = self._build_history("sender")
        self._history_by_recipient = self._build_history("recipient")
        
        salaries = [_as_float(u.get("salary")) for u in users.values() if _as_float(u.get("salary")) > 0]
        salaries.sort()
        self._global_median_salary = salaries[len(salaries)//2] if salaries else 35000.0

        all_distances = []
        for uid, locs in locations_by_user.items():
            u = users.get(uid, {})
            res_lat = _as_float(u.get("residence", {}).get("lat"))
            res_lng = _as_float(u.get("residence", {}).get("lng"))
            if res_lat and res_lng:
                for loc in locs:
                    lat = _as_float(loc.get("lat"))
                    lng = _as_float(loc.get("lng"))
                    if lat and lng:
                        all_distances.append(_haversine(res_lat, res_lng, lat, lng))
        all_distances.sort()
        self._global_median_distance = all_distances[len(all_distances)//2] if all_distances else 100.0

        all_velocities = []
        for user_history in self._history_by_sender.values():
            sorted_history = sorted(user_history, key=_timestamp_key)
            last_t = None
            for row in sorted_history:
                t = _parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"]))
                if last_t is not None and t is not None:
                    all_velocities.append((t - last_t).total_seconds())
                last_t = t
        all_velocities.sort()
        self._global_median_velocity = all_velocities[len(all_velocities)//2] if all_velocities else 86400.0

    def build(self, transaction: Dict[str, Any], index: int) -> TransactionContext:
        sender_id = _get_value(transaction, ["Sender ID", "sender_id", "sender id"])
        recipient_id = _get_value(transaction, ["Recipient ID", "recipient_id", "recipient id"])
        sender_key = str(sender_id) if sender_id else ""
        recipient_key = str(recipient_id) if recipient_id else ""
        sender_history = self._history_by_sender.get(sender_key, [])
        recipient_history = self._history_by_recipient.get(recipient_key, [])
        transaction_id = str(_get_value(transaction, ["Transaction ID", "transaction_id", "transaction id", "id"]) or "")

        timestamp = _parse_timestamp(_get_value(transaction, ["Timestamp", "timestamp", "Datetime", "datetime"]))
        
        def is_before(comm_ts, tx_ts):
            if comm_ts is None or tx_ts is None:
                return True
            # make both timezone aware or naive to compare
            if comm_ts.tzinfo is not None and tx_ts.tzinfo is None:
                return comm_ts.replace(tzinfo=None) <= tx_ts
            if comm_ts.tzinfo is None and tx_ts.tzinfo is not None:
                return comm_ts <= tx_ts.replace(tzinfo=None)
            return comm_ts <= tx_ts

        sender_history_before = [
            row for row in sender_history 
            if str(_get_value(row, ["Transaction ID", "transaction_id", "transaction id", "id"]) or "") != transaction_id
            and is_before(_parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"])), timestamp)
        ]
        recipient_history_before = [
            row for row in recipient_history 
            if str(_get_value(row, ["Transaction ID", "transaction_id", "transaction id", "id"]) or "") != transaction_id
            and is_before(_parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"])), timestamp)
        ]

        sender_conversations_before = [comm for comm in self._conversations_by_user.get(sender_key, []) if is_before(comm.timestamp, timestamp)]
        sender_messages_before = [comm for comm in self._messages_by_user.get(sender_key, []) if is_before(comm.timestamp, timestamp)]

        # Velocity stats for user
        intervals = []
        last_t = None
        for row in sorted(sender_history_before, key=_timestamp_key):
            t = _parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"]))
            if last_t is not None and t is not None:
                intervals.append((t - last_t).total_seconds())
            last_t = t
            
        vel_mean = mean(intervals) if intervals else 86400.0
        vel_std = stdev(intervals) if len(intervals) > 1 else vel_mean * 0.5
        velocity_stats = {"mean": vel_mean, "std": vel_std}

        # Location stats for user
        sender_profile = self._users.get(sender_key, {})
        residence = sender_profile.get("residence", {})
        res_lat = _as_float(residence.get("lat"))
        res_lng = _as_float(residence.get("lng"))
        
        distances = []
        for loc in self._locations_by_user.get(sender_key, []):
            loc_t = _parse_timestamp(loc.get("timestamp"))
            if is_before(loc_t, timestamp):
                lat = _as_float(loc.get("lat"))
                lng = _as_float(loc.get("lng"))
                if res_lat != 0.0 and res_lng != 0.0 and lat != 0.0 and lng != 0.0:
                    distances.append(_haversine(res_lat, res_lng, lat, lng))
                    
        dist_mean = mean(distances) if distances else 10.0
        dist_std = stdev(distances) if len(distances) > 1 else dist_mean * 0.5
        location_stats = {"mean": dist_mean, "std": dist_std}

        return TransactionContext(
            transaction=transaction,
            sender_profile=sender_profile,
            recipient_profile=self._users.get(recipient_key, {}),
            sender_history=sender_history_before,
            recipient_history=recipient_history_before,
            sender_locations=self._locations_by_user.get(sender_key, []),
            sender_conversations=sender_conversations_before,
            sender_messages=sender_messages_before,
            transaction_index=index,
            global_median_salary=self._global_median_salary,
            global_median_distance=self._global_median_distance,
            global_median_velocity=self._global_median_velocity,
            user_velocity_stats=velocity_stats,
            user_location_stats=location_stats,
        )

    def _build_history(self, role: str) -> Dict[str, List[Dict[str, Any]]]:
        key_names = [f"{role}_id", f"{role} id", f"{role.title()} ID"]
        history: Dict[str, List[Dict[str, Any]]] = {}
        for row in sorted(self._transactions, key=_timestamp_key):
            value = _get_value(row, key_names)
            if value is None:
                continue
            history.setdefault(str(value), []).append(row)
        return history

def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text)

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def score_transaction(context: TransactionContext) -> Dict[str, Any]:
    signals: List[FraudSignal] = []
    transaction = context.transaction
    amount = _as_float(_get_value(transaction, ["Amount", "amount"]))
    balance = _as_float(_get_value(transaction, ["Balance", "balance", "balance_after"]))
    tx_type = str(_get_value(transaction, ["Transaction Type", "transaction_type", "transaction type"]) or "").strip().lower()
    payment_method = str(_get_value(transaction, ["Payment Method", "payment_method", "payment method"]) or "").strip().lower()
    location = str(_get_value(transaction, ["Location", "location", "merchant", "merchant_name"]) or "").strip()
    timestamp = _parse_timestamp(_get_value(transaction, ["Timestamp", "timestamp", "Datetime", "datetime"]))
    
    sender_profile = context.sender_profile
    salary = _as_float(sender_profile.get("salary", 0))
    desc = sender_profile.get("description", "").lower()
    phishing_risk = any(k in desc for k in ["phishing", "hameçonnage", "dubious links", "too trusting", "trop confiant", "fall for", "scam", "click on"])

    sender_amounts = [_as_float(_get_value(row, ["Amount", "amount"])) for row in context.sender_history if _as_float(_get_value(row, ["Amount", "amount"])) > 0]
    avg_amount = mean(sender_amounts) if sender_amounts else amount
    std_amount = stdev(sender_amounts) if len(sender_amounts) > 1 else (avg_amount * 0.5 if avg_amount else 1.0)
    max_amount = max(sender_amounts) if sender_amounts else amount

    # Z-Score for amount (how many standard deviations from the mean is this transaction)
    amount_z_score = (amount - avg_amount) / (std_amount if std_amount > 0 else 1.0)

    # Age context (assuming year is 2087)
    birth_year = _as_float(sender_profile.get("birth_year", 2000))
    age = 2087 - birth_year

    # Economic-aware & Age-aware Amount heuristics using User-Specific Statistical Outliers
    is_probing = False
    
    if len(sender_amounts) > 2:
        if amount_z_score > 3.0:
            signals.append(FraudSignal("amount_spike_extreme", 4.5, f"amount {amount:.2f} is a statistical outlier (Z={amount_z_score:.1f})"))
        elif amount_z_score > 2.0:
            signals.append(FraudSignal("amount_spike", 3.0, f"amount {amount:.2f} is unusually high for user (Z={amount_z_score:.1f})"))
        
        # Probing transactions are usually very small, but shouldn't trigger on established recipients
        is_probing = amount < 5.0 and amount_z_score < -1.5
    else:
        # Fallback for users with very little history
        if sender_amounts and amount > avg_amount * 3:
            signals.append(FraudSignal("amount_spike_extreme", 4.0, f"amount {amount:.2f} is extreme vs average {avg_amount:.2f}"))
        elif sender_amounts and amount < 5.0:
            is_probing = True

    # Recipient heuristics (do this before evaluating probing)
    recent_sender = context.sender_history[-25:]
    prior_recipients = {
        str(_get_value(row, ["Recipient ID", "recipient_id", "recipient id"]) or "")
        for row in recent_sender
        if _get_value(row, ["Recipient ID", "recipient_id", "recipient id"]) is not None
    }
    recipient_id = str(_get_value(transaction, ["Recipient ID", "recipient_id", "recipient id"]) or "")
    is_new_recipient = recipient_id and prior_recipients and recipient_id not in prior_recipients
    
    if is_new_recipient:
        signals.append(FraudSignal("new_recipient", 2.0, f"recipient {recipient_id} not seen in recent sender history"))
        
    if is_probing and is_new_recipient:
        signals.append(FraudSignal("potential_probing", 3.0, f"very small amount {amount:.2f} to new recipient"))

    if sender_amounts and amount > max_amount * 1.1:
        signals.append(FraudSignal("historical_max_break", 3.5, f"amount {amount:.2f} exceeds sender max {max_amount:.2f}"))
    
    # Salary heuristics using Z-score equivalent or global fallback
    if salary > 0:
        monthly_salary = salary / 12
        if amount > monthly_salary * 1.5:
            signals.append(FraudSignal("salary_exceeded_extreme", 4.0, f"transaction exceeds 1.5x monthly salary"))
        elif amount > monthly_salary * 0.8:
            signals.append(FraudSignal("salary_exceeded_high", 2.5, f"transaction consumes most of monthly salary"))
    else:
        # Fallback to global median salary if unknown
        global_monthly = context.global_median_salary / 12
        if amount > global_monthly * 1.5:
            signals.append(FraudSignal("salary_exceeded_extreme_global", 3.5, f"transaction exceeds 1.5x global median monthly salary"))

    if balance >= 0 and amount > 0 and amount > max(balance, 1.0) * 0.90:
        signals.append(FraudSignal("balance_drain", 3.5, f"transaction consumes almost all remaining balance {balance:.2f}"))

    # Temporal heuristics
    if timestamp is not None and (timestamp.hour < 5 or timestamp.hour >= 23):
        day_hours = [
            _parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"]))
            for row in recent_sender
        ]
        baseline_night = sum(1 for item in day_hours if item is not None and (item.hour < 5 or item.hour >= 23))
        if recent_sender and baseline_night / max(len(recent_sender), 1) < 0.10:
            signals.append(FraudSignal("off_hours", 2.5, f"transaction occurs at atypical hour {timestamp.hour:02d}:00"))

    # Location / City mismatch using adaptive Z-scores for distance
    residence = sender_profile.get("residence", {})
    res_city = str(residence.get("city", "")).lower()
    res_lat = _as_float(residence.get("lat"))
    res_lng = _as_float(residence.get("lng"))
    
    # Check latest GPS ping relative to residence
    if context.sender_locations and res_lat != 0.0 and res_lng != 0.0:
        # get the most recent location before this transaction
        recent_locs = [loc for loc in context.sender_locations if _parse_timestamp(loc.get("timestamp")) and timestamp and _parse_timestamp(loc.get("timestamp")) <= timestamp]
        if recent_locs:
            last_loc = recent_locs[-1]
            last_lat = _as_float(last_loc.get("lat"))
            last_lng = _as_float(last_loc.get("lng"))
            
            if last_lat != 0.0 and last_lng != 0.0:
                dist_km = _haversine(res_lat, res_lng, last_lat, last_lng)
                dist_mean = context.user_location_stats["mean"]
                dist_std = context.user_location_stats["std"]
                
                # If user has very little location history, fallback to global median as a threshold guide
                if dist_std < 1.0 and dist_km > context.global_median_distance * 2:
                    signals.append(FraudSignal("distant_gps_ping_fallback", 2.5, f"recent GPS is far from residence ({dist_km:.0f}km)"))
                else:
                    dist_z_score = (dist_km - dist_mean) / (dist_std if dist_std > 0 else 1.0)
                    if dist_z_score > 3.0 and dist_km > context.global_median_distance:
                        signals.append(FraudSignal("distant_gps_ping_extreme", 3.5, f"recent GPS is a statistical outlier: {dist_km:.0f}km away from residence (Z={dist_z_score:.1f})"))
                    elif dist_z_score > 2.0 and dist_km > context.global_median_distance:
                        signals.append(FraudSignal("unusual_gps_ping", 2.5, f"recent GPS is {dist_km:.0f}km away from residence (Z={dist_z_score:.1f})"))

    if tx_type in {"in-person payment", "in person payment", "withdrawal", "prelievo"} and location:
        location_text = " ".join(str(_get_value(row, ["Location", "location"]) or "") for row in recent_sender[-20:]).lower()
        if location.lower() not in location_text and location_text:
            signals.append(FraudSignal("new_physical_location", 3.0, f"location {location} not in recent history"))
        
        # Checking GPS against residence if no prior GPS
        if res_city and res_city not in location.lower() and location.lower() not in res_city:
            signals.append(FraudSignal("city_mismatch", 2.5, f"location {location} differs from residence {res_city}"))

    # Rapid sequence (Velocity) using Z-scores
    if len(recent_sender) >= 1 and timestamp is not None:
        last_time = _parse_timestamp(_get_value(recent_sender[-1], ["Timestamp", "timestamp", "Datetime", "datetime"]))
        if last_time is not None:
            seconds = (timestamp - last_time).total_seconds()
            if seconds >= 0:
                vel_mean = context.user_velocity_stats["mean"]
                vel_std = context.user_velocity_stats["std"]
                
                # If user history is sparse, use global median velocity (approx 2,500,000s in Truman) or a minimum safety buffer
                vel_z_score = (seconds - vel_mean) / (vel_std if vel_std > 0 else 1.0)
                
                if vel_z_score < -2.0 and seconds < vel_mean * 0.1:
                    signals.append(FraudSignal("rapid_sequence_extreme", 4.0, f"transaction follows prior unusually fast for user (Z={vel_z_score:.1f}, {int(seconds)}s)"))
                elif vel_z_score < -1.5 and seconds < vel_mean * 0.2:
                    signals.append(FraudSignal("rapid_sequence", 2.5, f"transaction follows prior fast for user (Z={vel_z_score:.1f}, {int(seconds)}s)"))

    # Suspicious Recipient Collector Account
    recipient_volume = len(context.recipient_history)
    if recipient_volume > 10:
        unique_senders = {str(_get_value(row, ["Sender ID", "sender_id", "sender id"]) or "") for row in context.recipient_history[-20:]}
        if len(unique_senders) > max(4, recipient_volume * 0.4):
            signals.append(FraudSignal("collector_account_pattern", 3.5, "recipient receives funds from many distinct senders"))

    # We also add a baseline risk penalty for vulnerable users to bump them into review thresholds easily
    if phishing_risk or age > 75:
        signals.append(FraudSignal("vulnerable_user_profile", 1.5, f"user profile indicates vulnerability (age {age}, phishing_risk={phishing_risk})"))

    total_score = round(sum(signal.score for signal in signals), 2)
    decision_hint = "review"
    
    # Tuning the bounds dynamically based on the number of signals to minimize LLM token usage 
    # and ensure only ambiguous records hit the model
    if total_score >= 8.0:
        decision_hint = "flag"
    elif total_score <= 2.5:
        decision_hint = "allow"

    return {
        "signals": [signal.__dict__ for signal in signals],
        "total_score": total_score,
        "decision_hint": decision_hint,
        "baseline": {
            "sender_avg_amount": round(avg_amount, 2),
            "sender_max_amount": round(max_amount, 2),
            "sender_history_size": len(context.sender_history),
            "recipient_history_size": len(context.recipient_history),
        },
    }

def _timestamp_key(row: Dict[str, Any]) -> datetime:
    return _parse_timestamp(_get_value(row, ["Timestamp", "timestamp", "Datetime", "datetime"])) or datetime.min

def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None

def _as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0

def _get_value(row: Dict[str, Any], keys: List[str]) -> Any:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        match = lowered.get(key.lower())
        if match not in (None, ""):
            return match
    return None
