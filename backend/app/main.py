from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import Base, engine, get_db
from app.models import (
    Agent,
    AgentBalance,
    Alert,
    Case,
    Provider,
    Transaction,
)
from app.schemas import (
    AgentResponse,
    AlertGenerationResponse,
    AnomalyAlertResponse,
    CaseAssignmentRequest,
    CaseCreateRequest,
    CaseNoteRequest,
    CaseResponse,
    CaseStatusUpdateRequest,
    LiquidityForecastResponse,
    StoredAlertResponse,
    TransactionResponse,
    DemoScenarioResponse
)
from app.services.alert_engine import (
    generate_agent_alerts,
    serialize_alert,
)
from app.services.anomaly_detection import (
    detect_unusual_activity,
)
from app.services.case_management import (
    add_case_note,
    assign_case,
    create_case_from_alert,
    get_all_cases,
    get_case_by_id,
    update_case_status,
)
from app.services.forecasting import (
    calculate_liquidity_forecast,
)

from app.services.demo_scenarios import (
    inject_anomaly_burst,
    inject_full_demo,
    inject_liquidity_crisis,
)

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AgentPulse AI API",
    description=(
        "Multi-provider liquidity forecasting, unusual "
        "activity detection, alert generation, and "
        "human case coordination."
    ),
    version="0.5.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "AgentPulse AI",
        "status": "running",
        "version": "0.5.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "analytics": "ready",
        "alerts": "ready",
        "case_management": "ready",
    }


@app.get(
    "/api/agents",
    response_model=list[AgentResponse],
)
def get_agents(
    db: Session = Depends(get_db),
):
    return (
        db.query(Agent)
        .options(
            joinedload(Agent.balances)
            .joinedload(AgentBalance.provider)
        )
        .all()
    )


@app.get(
    "/api/agents/{agent_id}",
    response_model=AgentResponse,
)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
):
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
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return agent


@app.get(
    "/api/agents/{agent_id}/transactions",
    response_model=list[TransactionResponse],
)
def get_agent_transactions(
    agent_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return (
        db.query(Transaction)
        .filter(
            Transaction.agent_id == agent_id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(limit)
        .all()
    )


@app.get(
    "/api/agents/{agent_id}/liquidity-forecast",
    response_model=list[LiquidityForecastResponse],
)
def get_liquidity_forecast(
    agent_id: int,
    window_minutes: int = Query(
        default=60,
        ge=15,
        le=360,
    ),
    db: Session = Depends(get_db),
):
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
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return calculate_liquidity_forecast(
        db=db,
        agent=agent,
        window_minutes=window_minutes,
    )


@app.get(
    "/api/agents/{agent_id}/anomalies",
    response_model=list[AnomalyAlertResponse],
)
def get_agent_anomalies(
    agent_id: int,
    window_minutes: int = Query(
        default=30,
        ge=10,
        le=180,
    ),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return detect_unusual_activity(
        db=db,
        agent=agent,
        window_minutes=window_minutes,
    )


@app.post(
    "/api/agents/{agent_id}/generate-alerts",
    response_model=AlertGenerationResponse,
)
def create_agent_alerts(
    agent_id: int,
    window_minutes: int = Query(
        default=60,
        ge=15,
        le=180,
    ),
    db: Session = Depends(get_db),
):
    try:
        result = generate_agent_alerts(
            db=db,
            agent_id=agent_id,
            window_minutes=window_minutes,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    serialized_alerts = []

    for alert in result["alerts"]:
        agent = (
            db.query(Agent)
            .filter(Agent.id == alert.agent_id)
            .first()
        )

        provider = None

        if alert.provider_id is not None:
            provider = (
                db.query(Provider)
                .filter(
                    Provider.id == alert.provider_id
                )
                .first()
            )

        serialized_alerts.append(
            serialize_alert(
                alert=alert,
                agent=agent,
                provider=provider,
            )
        )

    return {
        "agent_id": result["agent_id"],
        "agent_code": result["agent_code"],
        "created_count": result["created_count"],
        "skipped_duplicate_count": result[
            "skipped_duplicate_count"
        ],
        "alerts": serialized_alerts,
    }


@app.get(
    "/api/alerts",
    response_model=list[StoredAlertResponse],
)
def get_alerts(
    agent_id: Optional[int] = Query(
        default=None,
        ge=1,
    ),
    provider_id: Optional[int] = Query(
        default=None,
        ge=1,
    ),
    severity: Optional[str] = Query(
        default=None,
    ),
    status: Optional[str] = Query(
        default=None,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Alert)

    if agent_id is not None:
        query = query.filter(
            Alert.agent_id == agent_id
        )

    if provider_id is not None:
        query = query.filter(
            Alert.provider_id == provider_id
        )

    if severity is not None:
        query = query.filter(
            Alert.severity == severity.lower()
        )

    if status is not None:
        query = query.filter(
            Alert.status == status.lower()
        )

    alerts = (
        query.order_by(
            Alert.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    results = []

    for alert in alerts:
        agent = (
            db.query(Agent)
            .filter(
                Agent.id == alert.agent_id
            )
            .first()
        )

        provider = None

        if alert.provider_id is not None:
            provider = (
                db.query(Provider)
                .filter(
                    Provider.id == alert.provider_id
                )
                .first()
            )

        results.append(
            serialize_alert(
                alert=alert,
                agent=agent,
                provider=provider,
            )
        )

    return results


@app.get(
    "/api/alerts/{alert_id}",
    response_model=StoredAlertResponse,
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    agent = (
        db.query(Agent)
        .filter(Agent.id == alert.agent_id)
        .first()
    )

    provider = None

    if alert.provider_id is not None:
        provider = (
            db.query(Provider)
            .filter(
                Provider.id == alert.provider_id
            )
            .first()
        )

    return serialize_alert(
        alert=alert,
        agent=agent,
        provider=provider,
    )


@app.post(
    "/api/alerts/{alert_id}/cases",
    response_model=CaseResponse,
)
def create_case(
    alert_id: int,
    payload: CaseCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_case_from_alert(
            db=db,
            alert_id=alert_id,
            owner_name=payload.owner_name,
            owner_role=payload.owner_role,
            priority=payload.priority,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.get(
    "/api/cases",
    response_model=list[CaseResponse],
)
def get_cases(
    status: Optional[str] = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    return get_all_cases(
        db=db,
        status=status,
    )


@app.get(
    "/api/cases/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case


@app.patch(
    "/api/cases/{case_id}/assignment",
    response_model=CaseResponse,
)
def update_case_assignment(
    case_id: int,
    payload: CaseAssignmentRequest,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return assign_case(
        db=db,
        case=case,
        owner_name=payload.owner_name,
        owner_role=payload.owner_role,
        actor=payload.actor,
    )


@app.patch(
    "/api/cases/{case_id}/status",
    response_model=CaseResponse,
)
def change_case_status(
    case_id: int,
    payload: CaseStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    try:
        return update_case_status(
            db=db,
            case=case,
            new_status=payload.status,
            actor=payload.actor,
            note=payload.note,
            resolution_summary=(
                payload.resolution_summary
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.post(
    "/api/cases/{case_id}/notes",
    response_model=CaseResponse,
)
def create_case_note(
    case_id: int,
    payload: CaseNoteRequest,
    db: Session = Depends(get_db),
):
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    try:
        return add_case_note(
            db=db,
            case=case,
            message=payload.message,
            actor=payload.actor,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    

@app.post(
    "/api/demo/agents/{agent_id}/liquidity-crisis",
    response_model=DemoScenarioResponse,
)
def create_liquidity_crisis_demo(
    agent_id: int,
    db: Session = Depends(get_db),
):
    try:
        return inject_liquidity_crisis(
            db=db,
            agent_id=agent_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@app.post(
    "/api/demo/agents/{agent_id}/anomaly-burst",
    response_model=DemoScenarioResponse,
)
def create_anomaly_burst_demo(
    agent_id: int,
    db: Session = Depends(get_db),
):
    try:
        return inject_anomaly_burst(
            db=db,
            agent_id=agent_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@app.post(
    "/api/demo/agents/{agent_id}/full-demo",
    response_model=DemoScenarioResponse,
)
def create_full_demo(
    agent_id: int,
    db: Session = Depends(get_db),
):
    try:
        return inject_full_demo(
            db=db,
            agent_id=agent_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error