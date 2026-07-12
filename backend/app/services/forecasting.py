from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Agent, Transaction


def utc_now_naive() -> datetime:
    """
    Return the current UTC time without timezone information.

    The existing SQLite database stores naive UTC timestamps,
    so this keeps datetime comparisons compatible.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def calculate_liquidity_forecast(
    db: Session,
    agent: Agent,
    window_minutes: int = 60,
) -> list[dict[str, Any]]:
    """
    Calculate provider-level liquidity pressure using:

    1. Recent transaction activity
    2. Seven-day same-hour historical activity
    3. Blended recent and historical demand rates

    Customer cash-in:
        Physical cash increases.
        Provider electronic float decreases.

    Customer cash-out:
        Physical cash decreases.
        Provider electronic float increases.
    """

    now = utc_now_naive()
    since_time = now - timedelta(minutes=window_minutes)
    historical_start = now - timedelta(days=7)

    forecasts: list[dict[str, Any]] = []

    for balance_record in agent.balances:
        provider = balance_record.provider

        recent_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.agent_id == agent.id,
                Transaction.provider_id == provider.id,
                Transaction.created_at >= since_time,
                Transaction.created_at <= now,
                Transaction.status == "success",
            )
            .all()
        )

        historical_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.agent_id == agent.id,
                Transaction.provider_id == provider.id,
                Transaction.created_at >= historical_start,
                Transaction.created_at < since_time,
                Transaction.status == "success",
            )
            .all()
        )

        recent_cash_in_total = sum(
            transaction.amount
            for transaction in recent_transactions
            if transaction.transaction_type == "cash_in"
        )

        recent_cash_out_total = sum(
            transaction.amount
            for transaction in recent_transactions
            if transaction.transaction_type == "cash_out"
        )

        recent_transaction_count = len(
            recent_transactions
        )

        recent_cash_in_rate = (
            recent_cash_in_total / window_minutes
        )

        recent_cash_out_rate = (
            recent_cash_out_total / window_minutes
        )

        same_hour_transactions = [
            transaction
            for transaction in historical_transactions
            if transaction.created_at.hour == now.hour
        ]

        historical_cash_in_total = sum(
            transaction.amount
            for transaction in same_hour_transactions
            if transaction.transaction_type == "cash_in"
        )

        historical_cash_out_total = sum(
            transaction.amount
            for transaction in same_hour_transactions
            if transaction.transaction_type == "cash_out"
        )

        historical_dates = {
            transaction.created_at.date()
            for transaction in same_hour_transactions
        }

        historical_day_count = max(
            len(historical_dates),
            1,
        )

        historical_minutes = (
            historical_day_count * 60
        )

        historical_cash_in_rate = (
            historical_cash_in_total
            / historical_minutes
        )

        historical_cash_out_rate = (
            historical_cash_out_total
            / historical_minutes
        )

        recent_float_drain_rate = max(
            recent_cash_in_rate
            - recent_cash_out_rate,
            0,
        )

        historical_float_drain_rate = max(
            historical_cash_in_rate
            - historical_cash_out_rate,
            0,
        )

        recent_cash_drain_rate = max(
            recent_cash_out_rate
            - recent_cash_in_rate,
            0,
        )

        historical_cash_drain_rate = max(
            historical_cash_out_rate
            - historical_cash_in_rate,
            0,
        )

        # Recent demand has more influence, while historical
        # activity helps avoid unstable one-window predictions.
        float_drain_rate = (
            recent_float_drain_rate * 0.75
            + historical_float_drain_rate * 0.25
        )

        physical_cash_drain_rate = (
            recent_cash_drain_rate * 0.75
            + historical_cash_drain_rate * 0.25
        )

        float_pressure_ratio = calculate_pressure_ratio(
            recent_rate=recent_float_drain_rate,
            historical_rate=historical_float_drain_rate,
        )

        cash_pressure_ratio = calculate_pressure_ratio(
            recent_rate=recent_cash_drain_rate,
            historical_rate=historical_cash_drain_rate,
        )

        float_shortage_minutes = None

        if float_drain_rate > 0:
            float_shortage_minutes = (
                balance_record.balance
                / float_drain_rate
            )

        cash_shortage_minutes = None

        if physical_cash_drain_rate > 0:
            cash_shortage_minutes = (
                agent.physical_cash
                / physical_cash_drain_rate
            )

        shortage_candidates: list[
            tuple[str, float]
        ] = []

        if float_shortage_minutes is not None:
            shortage_candidates.append(
                (
                    "provider_float",
                    float_shortage_minutes,
                )
            )

        if cash_shortage_minutes is not None:
            shortage_candidates.append(
                (
                    "physical_cash",
                    cash_shortage_minutes,
                )
            )

        risk_type = "stable"
        estimated_shortage_minutes = None

        if shortage_candidates:
            risk_type, estimated_shortage_minutes = min(
                shortage_candidates,
                key=lambda item: item[1],
            )

        projected_float_30m = max(
            balance_record.balance
            - (float_drain_rate * 30),
            0,
        )

        projected_cash_30m = max(
            agent.physical_cash
            - (physical_cash_drain_rate * 30),
            0,
        )

        historical_transaction_count = len(
            same_hour_transactions
        )

        confidence = calculate_confidence(
            recent_transaction_count=(
                recent_transaction_count
            ),
            historical_transaction_count=(
                historical_transaction_count
            ),
            historical_day_count=(
                historical_day_count
            ),
            data_status=balance_record.data_status,
        )

        severity = calculate_severity(
            estimated_shortage_minutes
        )

        if risk_type == "provider_float":
            explanation = (
                f"{provider.name} electronic balance is under "
                f"pressure because recent customer cash-in demand "
                f"is higher than cash-out demand. "
                f"The current float-drain pressure is "
                f"{format_ratio(float_pressure_ratio)} compared "
                f"with the seven-day same-hour baseline."
            )

            recommended_action = (
                "Review the provider balance and contact the "
                "assigned operations officer for approved "
                "liquidity support."
            )

        elif risk_type == "physical_cash":
            explanation = (
                f"{provider.name} cash-out demand is creating "
                f"pressure on the agent's shared physical cash. "
                f"The current cash-drain pressure is "
                f"{format_ratio(cash_pressure_ratio)} compared "
                f"with the seven-day same-hour baseline."
            )

            recommended_action = (
                "Review physical cash availability and coordinate "
                "an approved cash replenishment or operational "
                "response."
            )

        else:
            explanation = (
                f"No immediate liquidity shortage is predicted "
                f"for {provider.name}. Recent activity remains "
                f"within a manageable range when compared with "
                f"the seven-day same-hour baseline."
            )

            recommended_action = (
                "Continue monitoring transaction demand and "
                "data freshness."
            )

        if balance_record.data_status != "live":
            explanation += (
                f" Confidence is reduced because the provider "
                f"data status is "
                f"'{balance_record.data_status}'."
            )

        forecasts.append(
            {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "provider_code": provider.code,
                "current_provider_balance": round(
                    balance_record.balance,
                    2,
                ),
                "current_physical_cash": round(
                    agent.physical_cash,
                    2,
                ),
                "cash_in_total": round(
                    recent_cash_in_total,
                    2,
                ),
                "cash_out_total": round(
                    recent_cash_out_total,
                    2,
                ),
                "cash_in_rate_per_minute": round(
                    recent_cash_in_rate,
                    2,
                ),
                "cash_out_rate_per_minute": round(
                    recent_cash_out_rate,
                    2,
                ),
                "transaction_count": (
                    recent_transaction_count
                ),
                "risk_type": risk_type,
                "estimated_shortage_minutes": (
                    round(
                        estimated_shortage_minutes,
                        1,
                    )
                    if estimated_shortage_minutes
                    is not None
                    else None
                ),
                "projected_provider_balance_30m": round(
                    projected_float_30m,
                    2,
                ),
                "projected_physical_cash_30m": round(
                    projected_cash_30m,
                    2,
                ),
                "severity": severity,
                "confidence": confidence,
                "data_status": (
                    balance_record.data_status
                ),
                "last_updated": (
                    balance_record.last_updated
                ),
                "explanation": explanation,
                "recommended_action": (
                    recommended_action
                ),
                "human_review_required": severity
                in {
                    "critical",
                    "high",
                },
            }
        )

    return forecasts


def calculate_pressure_ratio(
    recent_rate: float,
    historical_rate: float,
) -> float | None:
    """
    Compare current pressure with the historical baseline.
    """

    if historical_rate <= 0:
        if recent_rate > 0:
            return None

        return 1.0

    return recent_rate / historical_rate


def format_ratio(
    ratio: float | None,
) -> str:
    if ratio is None:
        return (
            "significantly above the normal baseline"
        )

    return f"{ratio:.1f} times the normal level"


def calculate_confidence(
    recent_transaction_count: int,
    historical_transaction_count: int,
    historical_day_count: int,
    data_status: str,
) -> float:
    """
    Calculate confidence using recent sample size,
    historical sample size, data coverage, and freshness.
    """

    confidence = 0.45

    confidence += min(
        recent_transaction_count / 25,
        0.25,
    )

    confidence += min(
        historical_transaction_count / 80,
        0.15,
    )

    confidence += min(
        historical_day_count / 7,
        0.10,
    )

    if data_status == "live":
        confidence += 0.05

    elif data_status == "delayed":
        confidence -= 0.20

    elif data_status == "missing":
        confidence -= 0.40

    elif data_status == "conflicting":
        confidence -= 0.35

    confidence = max(
        0.20,
        min(confidence, 0.95),
    )

    return round(confidence, 2)


def calculate_severity(
    estimated_shortage_minutes: float | None,
) -> str:
    if estimated_shortage_minutes is None:
        return "low"

    if estimated_shortage_minutes <= 30:
        return "critical"

    if estimated_shortage_minutes <= 60:
        return "high"

    if estimated_shortage_minutes <= 120:
        return "medium"

    return "low"