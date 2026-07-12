from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Agent, AgentBalance, Transaction


def calculate_liquidity_forecast(
    db: Session,
    agent: Agent,
    window_minutes: int = 60,
) -> list[dict[str, Any]]:
    """
    Calculate provider-level liquidity pressure.

    Customer cash-in:
        Physical cash increases.
        Provider electronic float decreases.

    Customer cash-out:
        Physical cash decreases.
        Provider electronic float increases.
    """

    since_time = datetime.utcnow() - timedelta(minutes=window_minutes)

    forecasts: list[dict[str, Any]] = []

    for balance_record in agent.balances:
        provider = balance_record.provider

        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.agent_id == agent.id,
                Transaction.provider_id == provider.id,
                Transaction.created_at >= since_time,
                Transaction.status == "success",
            )
            .all()
        )

        cash_in_transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction_type == "cash_in"
        ]

        cash_out_transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction_type == "cash_out"
        ]

        cash_in_total = sum(
            transaction.amount
            for transaction in cash_in_transactions
        )

        cash_out_total = sum(
            transaction.amount
            for transaction in cash_out_transactions
        )

        transaction_count = len(transactions)

        cash_in_rate = cash_in_total / window_minutes
        cash_out_rate = cash_out_total / window_minutes

        # Provider e-float decreases when customers perform cash-in.
        float_drain_rate = max(
            cash_in_rate - cash_out_rate,
            0,
        )

        # Physical cash decreases when customers perform cash-out.
        physical_cash_drain_rate = max(
            cash_out_rate - cash_in_rate,
            0,
        )

        float_shortage_minutes = None

        if float_drain_rate > 0:
            float_shortage_minutes = (
                balance_record.balance / float_drain_rate
            )

        cash_shortage_minutes = None

        if physical_cash_drain_rate > 0:
            cash_shortage_minutes = (
                agent.physical_cash / physical_cash_drain_rate
            )

        shortage_candidates: list[tuple[str, float]] = []

        if float_shortage_minutes is not None:
            shortage_candidates.append(
                ("provider_float", float_shortage_minutes)
            )

        if cash_shortage_minutes is not None:
            shortage_candidates.append(
                ("physical_cash", cash_shortage_minutes)
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

        confidence = calculate_confidence(
            transaction_count=transaction_count,
            data_status=balance_record.data_status,
        )

        severity = calculate_severity(
            estimated_shortage_minutes
        )

        if risk_type == "provider_float":
            explanation = (
                f"{provider.name} electronic balance is under pressure. "
                f"Recent customer cash-in demand is higher than cash-out demand."
            )

            recommended_action = (
                "Review the provider balance and contact the assigned "
                "operations officer for approved liquidity support."
            )

        elif risk_type == "physical_cash":
            explanation = (
                f"{provider.name} cash-out demand is creating pressure "
                f"on the agent's shared physical cash."
            )

            recommended_action = (
                "Review physical cash availability and coordinate an "
                "approved cash replenishment or operational response."
            )

        else:
            explanation = (
                f"No immediate liquidity shortage is predicted for "
                f"{provider.name} using recent transaction activity."
            )

            recommended_action = (
                "Continue monitoring transaction demand and data freshness."
            )

        if balance_record.data_status != "live":
            explanation += (
                f" Confidence is reduced because the provider data status "
                f"is '{balance_record.data_status}'."
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
                "cash_in_total": round(cash_in_total, 2),
                "cash_out_total": round(cash_out_total, 2),
                "cash_in_rate_per_minute": round(
                    cash_in_rate,
                    2,
                ),
                "cash_out_rate_per_minute": round(
                    cash_out_rate,
                    2,
                ),
                "transaction_count": transaction_count,
                "risk_type": risk_type,
                "estimated_shortage_minutes": (
                    round(estimated_shortage_minutes, 1)
                    if estimated_shortage_minutes is not None
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
                "data_status": balance_record.data_status,
                "last_updated": balance_record.last_updated,
                "explanation": explanation,
                "recommended_action": recommended_action,
                "human_review_required": severity in {
                    "critical",
                    "high",
                },
            }
        )

    return forecasts


def calculate_confidence(
    transaction_count: int,
    data_status: str,
) -> float:
    confidence = 0.55

    confidence += min(
        transaction_count / 20,
        0.30,
    )

    if data_status == "delayed":
        confidence -= 0.25

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