import argparse
import random
from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Agent, AgentBalance, Provider, Transaction


def create_transaction(
    db,
    transaction_counter: int,
    agent: Agent,
    provider: Provider,
    transaction_type: str,
    amount: float,
    created_at: datetime,
    is_anomaly: bool = False,
    prefix: str = "TXN",
) -> int:
    transaction = Transaction(
        transaction_code=(
            f"{prefix}-{transaction_counter:06d}"
        ),
        agent_id=agent.id,
        provider_id=provider.id,
        transaction_type=transaction_type,
        amount=amount,
        status="success",
        created_at=created_at,
        is_simulated_anomaly=is_anomaly,
    )

    db.add(transaction)

    return transaction_counter + 1


def seed_database(reset: bool = False):
    if reset:
        print("Resetting existing database...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    rng = random.Random(42)

    try:
        existing_agents = db.query(Agent).count()

        if existing_agents > 0:
            print(
                "Database already contains data. "
                "Use --reset to recreate it."
            )
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

        provider_map = {
            provider.code: provider
            for provider in providers
        }

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

        now = datetime.utcnow()

        for agent in agents:
            for provider in providers:
                data_status = "live"

                if (
                    agent.agent_code == "AGT-002"
                    and provider.code == "NAGAD"
                ):
                    data_status = "delayed"

                last_updated = now

                if data_status == "delayed":
                    last_updated = (
                        now - timedelta(minutes=18)
                    )

                db.add(
                    AgentBalance(
                        agent_id=agent.id,
                        provider_id=provider.id,
                        balance=demo_balances[
                            agent.agent_code
                        ][provider.code],
                        data_status=data_status,
                        last_updated=last_updated,
                    )
                )

        db.commit()

        transaction_counter = 1
        week_start = now - timedelta(days=7)

        # Generate normal seven-day transaction history.
        for agent in agents:
            current_hour = week_start.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

            while current_hour <= now:
                hour = current_hour.hour
                weekday = current_hour.weekday()

                # Agent shops are mainly active from 8 AM to 10 PM.
                if hour < 8 or hour > 22:
                    current_hour += timedelta(hours=1)
                    continue

                hourly_count = 2

                if 10 <= hour <= 13:
                    hourly_count = 5
                elif 17 <= hour <= 21:
                    hourly_count = 7
                elif 8 <= hour <= 9:
                    hourly_count = 3
                elif 14 <= hour <= 16:
                    hourly_count = 4

                # Friday and Saturday have higher demand.
                if weekday in [4, 5]:
                    hourly_count += 2

                hourly_count = max(
                    1,
                    int(
                        rng.gauss(
                            hourly_count,
                            1.2,
                        )
                    ),
                )

                for _ in range(hourly_count):
                    provider = rng.choices(
                        providers,
                        weights=[50, 32, 18],
                        k=1,
                    )[0]

                    transaction_type = rng.choices(
                        ["cash_in", "cash_out"],
                        weights=[46, 54],
                        k=1,
                    )[0]

                    if rng.random() < 0.08:
                        amount = rng.randrange(
                            10000,
                            25001,
                            500,
                        )
                    else:
                        amount = rng.randrange(
                            500,
                            9501,
                            500,
                        )

                    created_at = (
                        current_hour
                        + timedelta(
                            minutes=rng.randint(0, 59),
                            seconds=rng.randint(0, 59),
                        )
                    )

                    if created_at > now:
                        continue

                    transaction_counter = (
                        create_transaction(
                            db=db,
                            transaction_counter=(
                                transaction_counter
                            ),
                            agent=agent,
                            provider=provider,
                            transaction_type=(
                                transaction_type
                            ),
                            amount=amount,
                            created_at=created_at,
                        )
                    )

                current_hour += timedelta(hours=1)

        agent_one = agents[0]
        bkash = provider_map["BKASH"]
        nagad = provider_map["NAGAD"]
        rocket = provider_map["ROCKET"]

        # Repeated amount anomaly during the recent period.
        for minute_offset in [28, 25, 22, 19, 16, 13]:
            transaction_counter = create_transaction(
                db=db,
                transaction_counter=transaction_counter,
                agent=agent_one,
                provider=nagad,
                transaction_type="cash_out",
                amount=12000,
                created_at=(
                    now
                    - timedelta(minutes=minute_offset)
                ),
                is_anomaly=True,
                prefix="DEMO-ANM",
            )

        # High-value transaction burst.
        high_value_amounts = [
            15000,
            18000,
            22000,
            17000,
        ]

        for index, amount in enumerate(
            high_value_amounts
        ):
            transaction_counter = create_transaction(
                db=db,
                transaction_counter=transaction_counter,
                agent=agent_one,
                provider=rocket,
                transaction_type="cash_out",
                amount=amount,
                created_at=(
                    now
                    - timedelta(
                        minutes=12 - index * 2
                    )
                ),
                is_anomaly=True,
                prefix="DEMO-HVB",
            )

        # Fresh bKash cash-in demand for liquidity forecast.
        liquidity_amounts = [
            15000,
            14500,
            16000,
            15500,
            15000,
            16500,
            14500,
            15000,
        ]

        for index, amount in enumerate(
            liquidity_amounts
        ):
            transaction_counter = create_transaction(
                db=db,
                transaction_counter=transaction_counter,
                agent=agent_one,
                provider=bkash,
                transaction_type="cash_in",
                amount=amount,
                created_at=(
                    now
                    - timedelta(minutes=index * 2)
                ),
                is_anomaly=False,
                prefix="DEMO-LIQ",
            )

        db.commit()

        total_transactions = (
            db.query(Transaction).count()
        )

        print("Seven-day synthetic data created.")
        print(
            f"Total transactions: "
            f"{total_transactions}"
        )
        print(
            f"Data period: {week_start} to {now}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing data and recreate database.",
    )

    arguments = parser.parse_args()

    seed_database(reset=arguments.reset)