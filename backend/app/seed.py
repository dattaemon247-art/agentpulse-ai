from datetime import datetime, timedelta
from random import choice, randint, uniform

from app.database import Base, SessionLocal, engine
from app.models import Agent, AgentBalance, Provider, Transaction


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing_agents = db.query(Agent).count()

        if existing_agents > 0:
            print("Database already contains data.")
            return

        providers = [
            Provider(name="bKash", code="BKASH"),
            Provider(name="Nagad", code="NAGAD"),
            Provider(name="Rocket", code="ROCKET"),
        ]

        db.add_all(providers)
        db.commit()

        for provider in providers:
            db.refresh(provider)

        agents = [
            Agent(
                agent_code="AGT-001",
                name="Rahman Telecom",
                area="Zindabazar, Sylhet",
                physical_cash=125000,
            ),
            Agent(
                agent_code="AGT-002",
                name="City Mobile Point",
                area="Ambarkhana, Sylhet",
                physical_cash=98000,
            ),
            Agent(
                agent_code="AGT-003",
                name="Sadia Enterprise",
                area="Subidbazar, Sylhet",
                physical_cash=145000,
            ),
        ]

        db.add_all(agents)
        db.commit()

        for agent in agents:
            db.refresh(agent)

        demo_balances = {
            "AGT-001": {
                "BKASH": 18500,
                "NAGAD": 72000,
                "ROCKET": 48000,
            },
            "AGT-002": {
                "BKASH": 65000,
                "NAGAD": 22000,
                "ROCKET": 37000,
            },
            "AGT-003": {
                "BKASH": 84000,
                "NAGAD": 76000,
                "ROCKET": 16000,
            },
        }

        for agent in agents:
            for provider in providers:
                balance = demo_balances[agent.agent_code][provider.code]

                data_status = "live"

                if (
                    agent.agent_code == "AGT-002"
                    and provider.code == "NAGAD"
                ):
                    data_status = "delayed"

                db.add(
                    AgentBalance(
                        agent_id=agent.id,
                        provider_id=provider.id,
                        balance=balance,
                        data_status=data_status,
                        last_updated=(
                            datetime.utcnow() - timedelta(minutes=18)
                            if data_status == "delayed"
                            else datetime.utcnow()
                        ),
                    )
                )

        db.commit()

        transaction_counter = 1
        now = datetime.utcnow()

        for agent in agents:
            for minute_offset in range(180, 0, -5):
                provider = choice(providers)

                transaction_type = choice(
                    ["cash_in", "cash_out", "cash_out"]
                )

                amount = round(
                    uniform(500, 8000) / 100
                ) * 100

                transaction = Transaction(
                    transaction_code=f"TXN-{transaction_counter:05d}",
                    agent_id=agent.id,
                    provider_id=provider.id,
                    transaction_type=transaction_type,
                    amount=amount,
                    status="success",
                    created_at=now - timedelta(minutes=minute_offset),
                    is_simulated_anomaly=False,
                )

                db.add(transaction)
                transaction_counter += 1

        agent_one = agents[0]
        bkash = next(
            provider
            for provider in providers
            if provider.code == "BKASH"
        )

        for minute_offset in [18, 15, 12, 9, 6, 3]:
            transaction = Transaction(
                transaction_code=f"TXN-{transaction_counter:05d}",
                agent_id=agent_one.id,
                provider_id=bkash.id,
                transaction_type="cash_out",
                amount=9500,
                status="success",
                created_at=now - timedelta(minutes=minute_offset),
                is_simulated_anomaly=True,
            )

            db.add(transaction)
            transaction_counter += 1

        for _ in range(4):
            transaction = Transaction(
                transaction_code=f"TXN-{transaction_counter:05d}",
                agent_id=agent_one.id,
                provider_id=bkash.id,
                transaction_type="cash_out",
                amount=randint(12000, 18000),
                status="success",
                created_at=now - timedelta(minutes=randint(1, 8)),
                is_simulated_anomaly=True,
            )

            db.add(transaction)
            transaction_counter += 1

        db.commit()

        print("Synthetic demo data created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()