from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Agent, Provider, Transaction


def detect_unusual_activity(
    db: Session,
    agent: Agent,
    window_minutes: int = 30,
) -> list[dict[str, Any]]:
    """
    Detect unusual transaction patterns using explainable rules.

    This module does not declare fraud.
    Every result is advisory and requires human review.
    """

    since_time = datetime.utcnow() - timedelta(
        minutes=window_minutes
    )

    recent_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.agent_id == agent.id,
            Transaction.created_at >= since_time,
            Transaction.status == "success",
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )

    providers = {
        provider.id: provider
        for provider in db.query(Provider).all()
    }

    alerts: list[dict[str, Any]] = []

    alerts.extend(
        detect_repeated_amounts(
            transactions=recent_transactions,
            providers=providers,
            window_minutes=window_minutes,
        )
    )

    alerts.extend(
        detect_high_value_bursts(
            transactions=recent_transactions,
            providers=providers,
            window_minutes=window_minutes,
        )
    )

    alerts.extend(
        detect_velocity_spikes(
            db=db,
            agent=agent,
            recent_transactions=recent_transactions,
            providers=providers,
            window_minutes=window_minutes,
        )
    )

    severity_order = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    alerts.sort(
        key=lambda alert: severity_order.get(
            alert["severity"],
            0,
        ),
        reverse=True,
    )

    return alerts


def detect_repeated_amounts(
    transactions: list[Transaction],
    providers: dict[int, Provider],
    window_minutes: int,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    grouped_transactions: dict[
        tuple[int, str], list[Transaction]
    ] = {}

    for transaction in transactions:
        key = (
            transaction.provider_id,
            transaction.transaction_type,
        )

        grouped_transactions.setdefault(
            key,
            [],
        ).append(transaction)

    for (
        provider_id,
        transaction_type,
    ), provider_transactions in grouped_transactions.items():
        amount_counts = Counter(
            transaction.amount
            for transaction in provider_transactions
        )

        for amount, count in amount_counts.items():
            if count < 4:
                continue

            provider = providers.get(provider_id)

            confidence = min(
                0.55 + (count * 0.06),
                0.94,
            )

            severity = (
                "high"
                if count >= 6
                else "medium"
            )

            alerts.append(
                {
                    "alert_type": "repeated_amount",
                    "provider_id": provider_id,
                    "provider_name": (
                        provider.name
                        if provider
                        else "Unknown"
                    ),
                    "severity": severity,
                    "confidence": round(confidence, 2),
                    "title": (
                        "Repeated transaction amount detected"
                    ),
                    "reason": (
                        f"{count} {transaction_type.replace('_', ' ')} "
                        f"transactions of BDT {amount:,.0f} occurred "
                        f"within {window_minutes} minutes."
                    ),
                    "evidence": {
                        "repeated_amount": amount,
                        "occurrence_count": count,
                        "transaction_type": transaction_type,
                        "window_minutes": window_minutes,
                    },
                    "possible_explanation": (
                        "This pattern may result from legitimate "
                        "customer demand, salary-day activity, market-day "
                        "activity, or repeated merchant payments."
                    ),
                    "recommended_action": (
                        "Review the related transactions and contact the "
                        "agent only if additional verification is required."
                    ),
                    "human_review_required": True,
                }
            )

    return alerts


def detect_high_value_bursts(
    transactions: list[Transaction],
    providers: dict[int, Provider],
    window_minutes: int,
    high_value_threshold: float = 10000,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    provider_groups: dict[
        int, list[Transaction]
    ] = {}

    for transaction in transactions:
        if transaction.amount >= high_value_threshold:
            provider_groups.setdefault(
                transaction.provider_id,
                [],
            ).append(transaction)

    for provider_id, high_value_transactions in (
        provider_groups.items()
    ):
        count = len(high_value_transactions)

        if count < 3:
            continue

        total_amount = sum(
            transaction.amount
            for transaction in high_value_transactions
        )

        provider = providers.get(provider_id)

        if count >= 6 or total_amount >= 100000:
            severity = "critical"
        elif count >= 4 or total_amount >= 60000:
            severity = "high"
        else:
            severity = "medium"

        confidence = min(
            0.60 + (count * 0.05),
            0.95,
        )

        alerts.append(
            {
                "alert_type": "high_value_burst",
                "provider_id": provider_id,
                "provider_name": (
                    provider.name
                    if provider
                    else "Unknown"
                ),
                "severity": severity,
                "confidence": round(confidence, 2),
                "title": (
                    "High-value transaction burst detected"
                ),
                "reason": (
                    f"{count} transactions of at least "
                    f"BDT {high_value_threshold:,.0f} occurred within "
                    f"{window_minutes} minutes, totalling "
                    f"BDT {total_amount:,.0f}."
                ),
                "evidence": {
                    "transaction_count": count,
                    "total_amount": total_amount,
                    "threshold": high_value_threshold,
                    "window_minutes": window_minutes,
                },
                "possible_explanation": (
                    "This may be caused by legitimate peak demand, "
                    "merchant settlements, salary disbursement, or a "
                    "local event."
                ),
                "recommended_action": (
                    "Compare the activity with the agent's historical "
                    "pattern and complete a human review before taking "
                    "any operational action."
                ),
                "human_review_required": True,
            }
        )

    return alerts


def detect_velocity_spikes(
    db: Session,
    agent: Agent,
    recent_transactions: list[Transaction],
    providers: dict[int, Provider],
    window_minutes: int,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    baseline_end = (
        datetime.utcnow()
        - timedelta(minutes=window_minutes)
    )

    baseline_start = (
        baseline_end
        - timedelta(minutes=window_minutes * 6)
    )

    baseline_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.agent_id == agent.id,
            Transaction.created_at >= baseline_start,
            Transaction.created_at < baseline_end,
            Transaction.status == "success",
        )
        .all()
    )

    for provider_id, provider in providers.items():
        recent_count = sum(
            1
            for transaction in recent_transactions
            if transaction.provider_id == provider_id
        )

        baseline_count = sum(
            1
            for transaction in baseline_transactions
            if transaction.provider_id == provider_id
        )

        baseline_window_count = baseline_count / 6

        if baseline_window_count <= 0:
            velocity_ratio = (
                float(recent_count)
                if recent_count > 0
                else 0
            )
        else:
            velocity_ratio = (
                recent_count / baseline_window_count
            )

        if recent_count < 5 or velocity_ratio < 2:
            continue

        if velocity_ratio >= 4:
            severity = "critical"
        elif velocity_ratio >= 3:
            severity = "high"
        else:
            severity = "medium"

        confidence = min(
            0.55 + (velocity_ratio * 0.08),
            0.94,
        )

        alerts.append(
            {
                "alert_type": "velocity_spike",
                "provider_id": provider_id,
                "provider_name": provider.name,
                "severity": severity,
                "confidence": round(confidence, 2),
                "title": (
                    "Transaction velocity spike detected"
                ),
                "reason": (
                    f"{recent_count} transactions occurred during the "
                    f"latest {window_minutes}-minute period. This is "
                    f"{velocity_ratio:.1f} times the recent baseline."
                ),
                "evidence": {
                    "recent_transaction_count": recent_count,
                    "baseline_average_count": round(
                        baseline_window_count,
                        2,
                    ),
                    "velocity_ratio": round(
                        velocity_ratio,
                        2,
                    ),
                    "window_minutes": window_minutes,
                },
                "possible_explanation": (
                    "Possible legitimate causes include salary day, "
                    "festival demand, network recovery, market hours, "
                    "or a temporary customer queue."
                ),
                "recommended_action": (
                    "Review transaction timing, amounts, and local "
                    "context. Escalate only when the evidence remains "
                    "unexplained."
                ),
                "human_review_required": True,
            }
        )

    return alerts