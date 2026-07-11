from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    area = Column(String, nullable=False)
    physical_cash = Column(Float, default=0)
    status = Column(String, default="active")

    balances = relationship(
        "AgentBalance",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    transactions = relationship(
        "Transaction",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)


class AgentBalance(Base):
    __tablename__ = "agent_balances"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)

    balance = Column(Float, default=0)
    data_status = Column(String, default="live")
    last_updated = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="balances")
    provider = relationship("Provider")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_code = Column(String, unique=True, index=True, nullable=False)

    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)

    transaction_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="success")
    created_at = Column(DateTime, default=datetime.utcnow)

    is_simulated_anomaly = Column(Boolean, default=False)

    agent = relationship("Agent", back_populates="transactions")
    provider = relationship("Provider")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)

    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    title = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    possible_explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    case_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    alert_id = Column(
        Integer,
        ForeignKey("alerts.id"),
        unique=True,
        nullable=False,
    )

    owner_name = Column(
        String,
        nullable=True,
    )

    owner_role = Column(
        String,
        nullable=True,
    )

    priority = Column(
        String,
        default="medium",
        nullable=False,
    )

    status = Column(
        String,
        default="new",
        nullable=False,
    )

    resolution_summary = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    events = relationship(
        "CaseEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseEvent.created_at",
    )


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False,
    )

    event_type = Column(
        String,
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    actor = Column(
        String,
        default="System",
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    case = relationship(
        "Case",
        back_populates="events",
    )