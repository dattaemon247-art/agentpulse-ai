from datetime import datetime
from typing import Optional
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProviderResponse(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    id: int
    balance: float
    data_status: str
    last_updated: datetime
    provider: ProviderResponse

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(BaseModel):
    id: int
    agent_code: str
    name: str
    area: str
    physical_cash: float
    status: str
    balances: list[BalanceResponse]

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: int
    transaction_code: str
    agent_id: int
    provider_id: int
    transaction_type: str
    amount: float
    status: str
    created_at: datetime
    is_simulated_anomaly: bool

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    id: int
    agent_id: int
    provider_id: Optional[int]
    alert_type: str
    severity: str
    confidence: float
    title: str
    reason: str
    evidence: Optional[str]
    possible_explanation: Optional[str]
    recommended_action: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class LiquidityForecastResponse(BaseModel):
    provider_id: int
    provider_name: str
    provider_code: str

    current_provider_balance: float
    current_physical_cash: float

    cash_in_total: float
    cash_out_total: float

    cash_in_rate_per_minute: float
    cash_out_rate_per_minute: float
    transaction_count: int

    risk_type: str
    estimated_shortage_minutes: Optional[float]

    projected_provider_balance_30m: float
    projected_physical_cash_30m: float

    severity: str
    confidence: float

    data_status: str
    last_updated: datetime

    explanation: str
    recommended_action: str
    human_review_required: bool

class AnomalyAlertResponse(BaseModel):
    alert_type: str
    provider_id: int
    provider_name: str
    severity: str
    confidence: float
    title: str
    reason: str
    evidence: dict[str, Any]
    possible_explanation: str
    recommended_action: str
    human_review_required: bool


class StoredAlertResponse(BaseModel):
    id: int
    agent_id: int
    agent_code: Optional[str] = None
    agent_name: Optional[str] = None

    provider_id: Optional[int]
    provider_name: Optional[str] = None

    alert_type: str
    severity: str
    confidence: float

    title: str
    reason: str
    evidence: dict[str, Any]

    possible_explanation: Optional[str]
    recommended_action: Optional[str]

    status: str
    human_review_required: bool
    created_at: datetime


class AlertGenerationResponse(BaseModel):
    agent_id: int
    agent_code: str
    created_count: int
    skipped_duplicate_count: int
    alerts: list[StoredAlertResponse]


class CaseCreateRequest(BaseModel):
    owner_name: Optional[str] = None
    owner_role: Optional[str] = None
    priority: str = "medium"


class CaseStatusUpdateRequest(BaseModel):
    status: str
    actor: str = "Operations User"
    note: Optional[str] = None
    resolution_summary: Optional[str] = None


class CaseNoteRequest(BaseModel):
    message: str
    actor: str = "Operations User"


class CaseAssignmentRequest(BaseModel):
    owner_name: str
    owner_role: str
    actor: str = "Operations Coordinator"


class CaseEventResponse(BaseModel):
    id: int
    event_type: str
    message: str
    actor: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseResponse(BaseModel):
    id: int
    case_code: str
    alert_id: int

    owner_name: Optional[str]
    owner_role: Optional[str]

    priority: str
    status: str
    resolution_summary: Optional[str]

    created_at: datetime
    updated_at: datetime

    events: list[CaseEventResponse]

    model_config = ConfigDict(from_attributes=True)




class DemoScenarioResponse(BaseModel):
    scenario: str
    agent_id: int
    message: str

    model_config = ConfigDict(
        extra="allow",
    )