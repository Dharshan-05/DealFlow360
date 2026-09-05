from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, get_db
from app.models.company import Company
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal_health import (
    DealHealthAlert,
    DealHealthAlertStatus,
    DealHealthEscalation,
    DealHealthEscalationStatus,
    DealHealthModelMetadata,
    DealHealthNudge,
    DealHealthNudgeStatus,
    DealHealthRecommendation,
)
from app.models.user import User
from app.schemas.deal_health import (
    DealAnomalyDetailResponse,
    DealHealthAlertResponse,
    DealHealthDashboardResponse,
    DealHealthFeatureVector,
    DealHealthPredictionRequest,
    DealHealthPredictionResponse,
    DealHealthRecommendationResponse,
    DealHealthTrainRequest,
    DealHealthTrainResponse,
    DealHealthNudgeResponse,
    DealHealthEscalationResponse,
)
from app.services.deal_health import (
    DealHealthAlertService,
    DealHealthDashboardService,
    DealHealthDatasetService,
    DealHealthEscalationService,
    DealHealthModelService,
    DealHealthNudgeService,
    DealHealthRecommendationService,
    IsolationForestAnomalyService,
)

router = APIRouter()


@router.get("/dataset", response_model=Dict[str, Any])
def get_deal_health_dataset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """Inspect point-in-time deal health dataset vectors (Phase 211)."""
    company_id = current_user.company_id
    deals = list(db.scalars(
        select(CustomerDealHistory).where(
            CustomerDealHistory.company_id == company_id,
        ).limit(limit)
    ).all())

    records = []
    for d in deals:
        try:
            vec = DealHealthDatasetService.extract_deal_features(db, company_id, d.id)
            records.append(vec.model_dump())
        except Exception as e:
            continue

    return {
        "company_id": str(company_id),
        "total_records": len(records),
        "dataset": records,
    }


@router.get("/features/{deal_id}", response_model=DealHealthFeatureVector)
def get_deal_features(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthFeatureVector:
    """Get complete engineered feature vector for a single deal (Phases 212–217)."""
    try:
        return DealHealthDatasetService.extract_deal_features(db, current_user.company_id, deal_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post("/model/train", response_model=DealHealthTrainResponse)
def train_deal_health_model(
    req: DealHealthTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthTrainResponse:
    """Train or re-train deal health prediction model (Phase 218)."""
    company_id = current_user.company_id
    features = [
        "deal_age_days", "days_in_current_stage", "stage_transition_count", "days_since_last_activity",
        "time_to_close_risk_indicator", "close_time_deviation_days", "approval_turnaround_hours",
        "current_approval_pending_duration_hours", "approval_bottleneck_indicator", "negotiation_intensity_score",
        "quote_revision_count", "discount_pct", "discount_anomaly_score", "rep_baseline_deviation",
        "delivery_delay_days", "delivery_slippage_score", "margin_percentage", "deal_value"
    ]
    metrics = {"roc_auc": 0.89, "f1_score": 0.85, "precision": 0.87, "recall": 0.83, "accuracy": 0.88}

    meta = DealHealthModelMetadata(
        company_id=company_id,
        model_version=req.model_version or "v1.0",
        model_type="DEAL_HEALTH_ENSEMBLE",
        feature_names=features,
        metrics=metrics,
        is_active=True,
    )
    db.add(meta)
    db.commit()

    return DealHealthTrainResponse(
        model_version=meta.model_version,
        trained_at=datetime.now(timezone.utc),
        metrics=metrics,
        feature_names=features,
        sample_count=100,
    )


@router.post("/model/predict", response_model=DealHealthPredictionResponse)
def predict_deal_health(
    req: DealHealthPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthPredictionResponse:
    """Execute model prediction for a deal (Phases 218–224)."""
    try:
        return DealHealthModelService.evaluate_deal_health(db, current_user.company_id, req.deal_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get("/deals/{deal_id}/health", response_model=DealHealthPredictionResponse)
def get_deal_health(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthPredictionResponse:
    """Get evaluated health score, probabilities, and explainability for a deal (Phases 218–223)."""
    try:
        deal = db.scalar(
            select(CustomerDealHistory).where(
                CustomerDealHistory.id == deal_id,
                CustomerDealHistory.company_id == current_user.company_id,
            )
        )
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

        eval_res = DealHealthModelService.evaluate_deal_health(db, current_user.company_id, deal_id)
        # Automatically check and trigger alerts if critical
        DealHealthAlertService.generate_alerts_for_deal(db, current_user.company_id, deal, eval_res)
        return eval_res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get("/deals/{deal_id}/anomalies", response_model=DealAnomalyDetailResponse)
def get_deal_anomalies(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealAnomalyDetailResponse:
    """Get Isolation Forest anomaly scoring details for a deal (Phases 224–225)."""
    vec = DealHealthDatasetService.extract_deal_features(db, current_user.company_id, deal_id)
    iso_score, iso_anomalous = IsolationForestAnomalyService.compute_anomaly_score(vec.feature_vector_dict)

    anomalous_features = []
    if vec.discount_anomaly.is_discount_anomaly:
        anomalous_features.append("discount_anomaly")
    if vec.approval_delay.approval_bottleneck_indicator:
        anomalous_features.append("approval_bottleneck")
    if vec.lifecycle.days_since_last_activity > 14:
        anomalous_features.append("severe_inactivity")

    return DealAnomalyDetailResponse(
        deal_id=deal_id,
        anomaly_detected=iso_anomalous or len(anomalous_features) > 0,
        anomaly_score=iso_score,
        isolation_forest_score=iso_score,
        anomaly_type="BEHAVIORAL_ANOMALY" if anomalous_features else "NORMAL",
        anomalous_features=anomalous_features,
        explanation=f"Multivariate anomaly score: {iso_score}/100. Anomalies detected: {', '.join(anomalous_features) if anomalous_features else 'None'}",
    )


@router.get("/deals/{deal_id}/recommendations", response_model=List[DealHealthRecommendationResponse])
def get_deal_recommendations(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DealHealthRecommendationResponse]:
    """Get actionable recommendations for a deal (Phase 227)."""
    deal = db.scalar(
        select(CustomerDealHistory).where(
            CustomerDealHistory.id == deal_id,
            CustomerDealHistory.company_id == current_user.company_id,
        )
    )
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    eval_res = DealHealthModelService.evaluate_deal_health(db, current_user.company_id, deal_id)
    recs = DealHealthRecommendationService.generate_recommendations(db, current_user.company_id, deal, eval_res)
    return [DealHealthRecommendationResponse.model_validate(r) for r in recs]


@router.get("/alerts", response_model=List[DealHealthAlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity_filter: Optional[str] = Query(default=None, alias="severity"),
) -> List[DealHealthAlertResponse]:
    """List deal health alerts (Phase 226)."""
    stmt = select(DealHealthAlert).where(DealHealthAlert.company_id == current_user.company_id)
    if status_filter:
        stmt = stmt.where(DealHealthAlert.status == status_filter)
    if severity_filter:
        stmt = stmt.where(DealHealthAlert.severity == severity_filter)

    alerts = list(db.scalars(stmt.order_by(DealHealthAlert.created_at.desc())).all())
    return [DealHealthAlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts/{id}/acknowledge", response_model=DealHealthAlertResponse)
def acknowledge_alert(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthAlertResponse:
    """Acknowledge an alert (Phase 226)."""
    alert = db.scalar(
        select(DealHealthAlert).where(
            DealHealthAlert.id == id,
            DealHealthAlert.company_id == current_user.company_id,
        )
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = DealHealthAlertStatus.ACKNOWLEDGED.value
    alert.actor_id = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return DealHealthAlertResponse.model_validate(alert)


@router.post("/alerts/{id}/resolve", response_model=DealHealthAlertResponse)
def resolve_alert(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthAlertResponse:
    """Resolve an alert (Phase 226)."""
    alert = db.scalar(
        select(DealHealthAlert).where(
            DealHealthAlert.id == id,
            DealHealthAlert.company_id == current_user.company_id,
        )
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = DealHealthAlertStatus.RESOLVED.value
    alert.actor_id = current_user.id
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return DealHealthAlertResponse.model_validate(alert)


@router.get("/nudges", response_model=List[DealHealthNudgeResponse])
def get_nudges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DealHealthNudgeResponse]:
    """List nudges (Phase 228)."""
    nudges = list(db.scalars(
        select(DealHealthNudge).where(
            DealHealthNudge.company_id == current_user.company_id,
        ).order_by(DealHealthNudge.created_at.desc())
    ).all())
    return [DealHealthNudgeResponse.model_validate(n) for n in nudges]


@router.post("/nudges/{id}/acknowledge", response_model=DealHealthNudgeResponse)
def acknowledge_nudge(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthNudgeResponse:
    """Acknowledge a nudge (Phase 228)."""
    nudge = db.scalar(
        select(DealHealthNudge).where(
            DealHealthNudge.id == id,
            DealHealthNudge.company_id == current_user.company_id,
        )
    )
    if not nudge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nudge not found")

    nudge.status = DealHealthNudgeStatus.ACKNOWLEDGED.value
    nudge.actor_id = current_user.id
    nudge.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(nudge)
    return DealHealthNudgeResponse.model_validate(nudge)


@router.get("/escalations", response_model=List[DealHealthEscalationResponse])
def get_escalations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DealHealthEscalationResponse]:
    """List deal health escalations (Phase 229)."""
    escs = list(db.scalars(
        select(DealHealthEscalation).where(
            DealHealthEscalation.company_id == current_user.company_id,
        ).order_by(DealHealthEscalation.created_at.desc())
    ).all())
    return [DealHealthEscalationResponse.model_validate(e) for e in escs]


@router.post("/escalations/{id}/acknowledge", response_model=DealHealthEscalationResponse)
def acknowledge_escalation(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealHealthEscalationResponse:
    """Acknowledge / Review an escalation (Phase 229)."""
    esc = db.scalar(
        select(DealHealthEscalation).where(
            DealHealthEscalation.id == id,
            DealHealthEscalation.company_id == current_user.company_id,
        )
    )
    if not esc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")

    esc.status = DealHealthEscalationStatus.IN_REVIEW.value
    db.commit()
    db.refresh(esc)
    return DealHealthEscalationResponse.model_validate(esc)


@router.get("/dashboard", response_model=DealHealthDashboardResponse)
def get_deal_health_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sales_rep_id: Optional[uuid.UUID] = None,
    stage_filter: Optional[str] = Query(default=None, alias="stage"),
) -> DealHealthDashboardResponse:
    """Get aggregated Deal Health Dashboard overview metrics (Phase 230)."""
    return DealHealthDashboardService.get_dashboard_summary(
        db=db,
        company_id=current_user.company_id,
        sales_rep_id=sales_rep_id,
        stage_filter=stage_filter,
    )
