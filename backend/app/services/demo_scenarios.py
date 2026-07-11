from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import (
    Agent,
    AgentBalance,
    Provider,
    Transaction,
)


def inject_liquidity_crisis(
    db: Session,
    agent_id: int,
) -> dict[str, Any]:
    """
    Create fresh bKash cash-in demand so that provider
    electronic float is predicted to run out quickly.
    """

    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise ValueError("Agent not found")

    bkash = (
        db.query(Provider)
        .filter(Provider.code == "BKASH")
        .first()
    )

    if not bkash:
        raise ValueError("bKash provider not found")

    balance_record = (
        db.query(AgentBalance)
        .filter(
            AgentBalance.agent_id == agent_id,
            AgentBalance.provider_id == bkash.id,
        )
        .first()
    )

    if not balance_record:
        raise ValueError(
            "Agent bKash balance record not found"
        )

    # Keep the current balance deliberately low.
    balance_record.balance = 18000
    balance_record.data_status = "live"
    balance_record.last_updated = datetime.utcnow()

    now = datetime.utcnow()
    created_transactions = []

    # Customer cash-in drains agent's provider e-float.
    amounts = [
        15000,
        14500,
        16000,
        15500,
        15000,
        16500,
        14500,
        15000,
    ]

    for index, amount in enumerate(amounts):
        transaction = Transaction(
            transaction_code=(
                f"DEMO-LIQ-{uuid4().hex[:12].upper()}"
            ),
            agent_id=agent.id,
            provider_id=bkash.id,
            transaction_type="cash_in",
            amount=amount,
            status="success",
            created_at=(
                now - timedelta(minutes=index * 2)
            ),
            is_simulated_anomaly=False,
        )

        db.add(transaction)
        created_transactions.append(transaction)

    db.commit()

    return {
        "scenario": "liquidity_crisis",
        "agent_id": agent.id,
        "provider": bkash.name,
        "transactions_created": len(
            created_transactions
        ),
        "provider_balance": balance_record.balance,
        "message": (
            "Fresh bKash liquidity crisis injected. "
            "Run the 60-minute forecast again."
        ),
    }


def inject_anomaly_burst(
    db: Session,
    agent_id: int,
) -> dict[str, Any]:
    """
    Create recent Nagad transactions that trigger:
    - repeated amount detection
    - high-value burst detection
    - transaction velocity spike detection
    """

    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise ValueError("Agent not found")

    nagad = (
        db.query(Provider)
        .filter(Provider.code == "NAGAD")
        .first()
    )

    if not nagad:
        raise ValueError("Nagad provider not found")

    balance_record = (
        db.query(AgentBalance)
        .filter(
            AgentBalance.agent_id == agent_id,
            AgentBalance.provider_id == nagad.id,
        )
        .first()
    )

    if balance_record:
        balance_record.data_status = "live"
        balance_record.last_updated = datetime.utcnow()

    now = datetime.utcnow()
    created_transactions = []

    # Six identical transactions trigger both repeated amount
    # and high-value burst rules.
    for index in range(6):
        transaction = Transaction(
            transaction_code=(
                f"DEMO-ANM-{uuid4().hex[:12].upper()}"
            ),
            agent_id=agent.id,
            provider_id=nagad.id,
            transaction_type="cash_out",
            amount=12000,
            status="success",
            created_at=(
                now - timedelta(minutes=index)
            ),
            is_simulated_anomaly=True,
        )

        db.add(transaction)
        created_transactions.append(transaction)

    # Additional transactions increase recent velocity.
    extra_amounts = [
        3500,
        4200,
        5100,
        6800,
        7400,
        8300,
    ]

    for index, amount in enumerate(extra_amounts):
        transaction = Transaction(
            transaction_code=(
                f"DEMO-VEL-{uuid4().hex[:12].upper()}"
            ),
            agent_id=agent.id,
            provider_id=nagad.id,
            transaction_type="cash_out",
            amount=amount,
            status="success",
            created_at=(
                now - timedelta(
                    minutes=7 + index
                )
            ),
            is_simulated_anomaly=True,
        )

        db.add(transaction)
        created_transactions.append(transaction)

    db.commit()

    return {
        "scenario": "anomaly_burst",
        "agent_id": agent.id,
        "provider": nagad.name,
        "transactions_created": len(
            created_transactions
        ),
        "message": (
            "Fresh anomaly burst injected. "
            "Run anomaly detection or Generate Alerts."
        ),
    }


def inject_full_demo(
    db: Session,
    agent_id: int,
) -> dict[str, Any]:
    liquidity_result = inject_liquidity_crisis(
        db=db,
        agent_id=agent_id,
    )

    anomaly_result = inject_anomaly_burst(
        db=db,
        agent_id=agent_id,
    )

    return {
        "scenario": "full_demo",
        "agent_id": agent_id,
        "liquidity": liquidity_result,
        "anomaly": anomaly_result,
        "message": (
            "Full demo scenario injected successfully. "
            "Refresh forecasts and generate alerts."
        ),
    }