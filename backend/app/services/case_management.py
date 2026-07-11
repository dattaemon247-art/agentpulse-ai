from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Alert, Case, CaseEvent


ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


ALLOWED_STATUS_TRANSITIONS = {
    "new": {
        "acknowledged",
        "assigned",
    },
    "acknowledged": {
        "assigned",
        "investigating",
    },
    "assigned": {
        "acknowledged",
        "investigating",
        "escalated",
    },
    "investigating": {
        "escalated",
        "resolved",
    },
    "escalated": {
        "investigating",
        "resolved",
    },
    "resolved": {
        "closed",
        "investigating",
    },
    "closed": set(),
}


def create_case_from_alert(
    db: Session,
    alert_id: int,
    owner_name: str | None = None,
    owner_role: str | None = None,
    priority: str = "medium",
) -> Case:
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise ValueError("Alert not found")

    existing_case = (
        db.query(Case)
        .filter(Case.alert_id == alert_id)
        .first()
    )

    if existing_case:
        return get_case_by_id(
            db=db,
            case_id=existing_case.id,
        )

    priority = priority.lower().strip()

    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(
            "Priority must be low, medium, high, or critical."
        )

    next_number = db.query(Case).count() + 1

    case = Case(
        case_code=f"CASE-{next_number:05d}",
        alert_id=alert_id,
        owner_name=owner_name,
        owner_role=owner_role,
        priority=priority,
        status="assigned" if owner_name else "new",
    )

    db.add(case)
    db.flush()

    db.add(
        CaseEvent(
            case_id=case.id,
            event_type="created",
            message=(
                f"Case created from alert #{alert_id} "
                f"with {priority} priority."
            ),
            actor="System",
        )
    )

    if owner_name:
        db.add(
            CaseEvent(
                case_id=case.id,
                event_type="assigned",
                message=(
                    f"Case assigned to {owner_name} "
                    f"({owner_role or 'Role not specified'})."
                ),
                actor="System",
            )
        )

    alert.status = (
        "assigned"
        if owner_name
        else "new"
    )

    db.commit()

    return get_case_by_id(
        db=db,
        case_id=case.id,
    )


def get_case_by_id(
    db: Session,
    case_id: int,
) -> Case | None:
    return (
        db.query(Case)
        .options(
            joinedload(Case.events)
        )
        .filter(Case.id == case_id)
        .first()
    )


def get_all_cases(
    db: Session,
    status: str | None = None,
) -> list[Case]:
    query = (
        db.query(Case)
        .options(
            joinedload(Case.events)
        )
    )

    if status:
        query = query.filter(
            Case.status == status.lower()
        )

    return (
        query.order_by(
            Case.created_at.desc()
        )
        .all()
    )


def assign_case(
    db: Session,
    case: Case,
    owner_name: str,
    owner_role: str,
    actor: str,
) -> Case:
    previous_owner = case.owner_name

    case.owner_name = owner_name
    case.owner_role = owner_role
    case.updated_at = datetime.utcnow()

    if case.status in {
        "new",
        "acknowledged",
    }:
        case.status = "assigned"

    message = (
        f"Case assigned to {owner_name} "
        f"({owner_role})."
    )

    if previous_owner:
        message = (
            f"Case reassigned from {previous_owner} "
            f"to {owner_name} ({owner_role})."
        )

    db.add(
        CaseEvent(
            case_id=case.id,
            event_type="assigned",
            message=message,
            actor=actor,
        )
    )

    alert = (
        db.query(Alert)
        .filter(Alert.id == case.alert_id)
        .first()
    )

    if alert:
        alert.status = case.status

    db.commit()

    return get_case_by_id(
        db=db,
        case_id=case.id,
    )


def update_case_status(
    db: Session,
    case: Case,
    new_status: str,
    actor: str,
    note: str | None = None,
    resolution_summary: str | None = None,
) -> Case:
    new_status = new_status.lower().strip()
    current_status = case.status.lower()

    allowed_statuses = (
        ALLOWED_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Cannot move case from '{current_status}' "
            f"to '{new_status}'."
        )

    if new_status == "resolved":
        if not resolution_summary:
            raise ValueError(
                "Resolution summary is required "
                "when resolving a case."
            )

        case.resolution_summary = resolution_summary

    case.status = new_status
    case.updated_at = datetime.utcnow()

    message = (
        f"Status changed from {current_status} "
        f"to {new_status}."
    )

    if note:
        message += f" Note: {note}"

    if resolution_summary:
        message += (
            f" Resolution: {resolution_summary}"
        )

    db.add(
        CaseEvent(
            case_id=case.id,
            event_type="status_changed",
            message=message,
            actor=actor,
        )
    )

    alert = (
        db.query(Alert)
        .filter(Alert.id == case.alert_id)
        .first()
    )

    if alert:
        alert.status = new_status

    db.commit()

    return get_case_by_id(
        db=db,
        case_id=case.id,
    )


def add_case_note(
    db: Session,
    case: Case,
    message: str,
    actor: str,
) -> Case:
    clean_message = message.strip()

    if not clean_message:
        raise ValueError(
            "Case note cannot be empty."
        )

    db.add(
        CaseEvent(
            case_id=case.id,
            event_type="note",
            message=clean_message,
            actor=actor,
        )
    )

    case.updated_at = datetime.utcnow()

    db.commit()

    return get_case_by_id(
        db=db,
        case_id=case.id,
    )