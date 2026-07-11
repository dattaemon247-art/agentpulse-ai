import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models import (
    Agent,
    AgentBalance,
    Alert,
    Provider,
)
from app.services.anomaly_detection import detect_unusual_activity
from app.services.forecasting import calculate_liquidity_forecast


def generate_agent_alerts(
    db: Session,
    agent_id: int,
    window_minutes: int = 60,
) -> dict[str, Any]:
    """
    Generate advisory alerts from liquidity forecasts
    and unusual-activity rules.

    The function avoids creating the same alert repeatedly
    within a short time window.
    """

    agent = (
        db.query(Agent)
        .options(
            joinedload(Agent.balances)
            .joinedload(AgentBalance.provider)
        )
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise ValueError("Agent not found")

    forecasts = calculate_liquidity_forecast(
        db=db,
        agent=agent,
        window_minutes=window_minutes,
    )

    anomalies = detect_unusual_activity(
        db=db,
        agent=agent,
        window_minutes=min(window_minutes, 180),
    )

    created_alerts: list[Alert] = []
    skipped_duplicates = 0

    # Create liquidity alerts
    for forecast in forecasts:
        estimated_minutes = forecast[
            "estimated_shortage_minutes"
        ]

        if estimated_minutes is None:
            continue

        if forecast["severity"] not in {
            "critical",
            "high",
            "medium",
        }:
            continue

        risk_type = forecast["risk_type"]
        provider_name = forecast["provider_name"]

        if risk_type == "provider_float":
            alert_type = "provider_float_shortage"
            title = (
                f"{provider_name} electronic balance "
                f"shortage predicted"
            )

        elif risk_type == "physical_cash":
            alert_type = "physical_cash_shortage"
            title = (
                f"Physical cash pressure linked to "
                f"{provider_name}"
            )

        else:
            continue

        reason = (
            f"Estimated service pressure may occur in "
            f"approximately {estimated_minutes:.1f} minutes. "
            f"{forecast['explanation']}"
        )

        evidence = {
            "risk_type": risk_type,
            "estimated_shortage_minutes": estimated_minutes,
            "current_provider_balance": forecast[
                "current_provider_balance"
            ],
            "current_physical_cash": forecast[
                "current_physical_cash"
            ],
            "cash_in_total": forecast["cash_in_total"],
            "cash_out_total": forecast["cash_out_total"],
            "transaction_count": forecast[
                "transaction_count"
            ],
            "data_status": forecast["data_status"],
            "window_minutes": window_minutes,
        }

        alert = create_alert_if_not_duplicate(
            db=db,
            agent_id=agent.id,
            provider_id=forecast["provider_id"],
            alert_type=alert_type,
            severity=forecast["severity"],
            confidence=forecast["confidence"],
            title=title,
            reason=reason,
            evidence=evidence,
            possible_explanation=(
                "Demand may be influenced by legitimate local "
                "events, salary-day activity, market demand, "
                "festival activity, or temporary customer queues."
            ),
            recommended_action=forecast[
                "recommended_action"
            ],
        )

        if alert:
            created_alerts.append(alert)
        else:
            skipped_duplicates += 1

    # Create unusual-activity alerts
    for anomaly in anomalies:
        alert = create_alert_if_not_duplicate(
            db=db,
            agent_id=agent.id,
            provider_id=anomaly["provider_id"],
            alert_type=anomaly["alert_type"],
            severity=anomaly["severity"],
            confidence=anomaly["confidence"],
            title=anomaly["title"],
            reason=anomaly["reason"],
            evidence=anomaly["evidence"],
            possible_explanation=anomaly[
                "possible_explanation"
            ],
            recommended_action=anomaly[
                "recommended_action"
            ],
        )

        if alert:
            created_alerts.append(alert)
        else:
            skipped_duplicates += 1

    db.commit()

    for alert in created_alerts:
        db.refresh(alert)

    return {
        "agent_id": agent.id,
        "agent_code": agent.agent_code,
        "created_count": len(created_alerts),
        "skipped_duplicate_count": skipped_duplicates,
        "alerts": created_alerts,
    }


def create_alert_if_not_duplicate(
    db: Session,
    agent_id: int,
    provider_id: int | None,
    alert_type: str,
    severity: str,
    confidence: float,
    title: str,
    reason: str,
    evidence: dict[str, Any],
    possible_explanation: str,
    recommended_action: str,
) -> Alert | None:
    """
    Prevent the same open alert type from being created
    repeatedly within the last ten minutes.
    """

    duplicate_window_start = (
        datetime.utcnow() - timedelta(minutes=10)
    )

    duplicate_query = db.query(Alert).filter(
        Alert.agent_id == agent_id,
        Alert.alert_type == alert_type,
        Alert.created_at >= duplicate_window_start,
        Alert.status.in_(
            [
                "new",
                "acknowledged",
                "assigned",
                "investigating",
                "escalated",
            ]
        ),
    )

    if provider_id is None:
        duplicate_query = duplicate_query.filter(
            Alert.provider_id.is_(None)
        )
    else:
        duplicate_query = duplicate_query.filter(
            Alert.provider_id == provider_id
        )

    existing_alert = duplicate_query.first()

    if existing_alert:
        return None

    alert = Alert(
        agent_id=agent_id,
        provider_id=provider_id,
        alert_type=alert_type,
        severity=severity,
        confidence=confidence,
        title=title,
        reason=reason,
        evidence=json.dumps(
            evidence,
            ensure_ascii=False,
        ),
        possible_explanation=possible_explanation,
        recommended_action=recommended_action,
        status="new",
    )

    db.add(alert)

    return alert


def serialize_alert(
    alert: Alert,
    agent: Agent | None = None,
    provider: Provider | None = None,
) -> dict[str, Any]:
    try:
        evidence = (
            json.loads(alert.evidence)
            if alert.evidence
            else {}
        )
    except json.JSONDecodeError:
        evidence = {
            "raw_evidence": alert.evidence,
        }

    return {
        "id": alert.id,
        "agent_id": alert.agent_id,
        "agent_code": (
            agent.agent_code
            if agent
            else None
        ),
        "agent_name": (
            agent.name
            if agent
            else None
        ),
        "provider_id": alert.provider_id,
        "provider_name": (
            provider.name
            if provider
            else None
        ),
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "confidence": alert.confidence,
        "title": alert.title,
        "reason": alert.reason,
        "evidence": evidence,
        "possible_explanation": (
            alert.possible_explanation
        ),
        "recommended_action": (
            alert.recommended_action
        ),
        "status": alert.status,
        "human_review_required": True,
        "created_at": alert.created_at,
    }