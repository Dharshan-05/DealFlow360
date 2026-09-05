from typing import Any, Dict, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.schemas.deal_health import (
    DealAnomalyDetailResponse,
    DealHealthAlertResponse,
    DealHealthDashboardResponse,
    DealHealthFeatureVector,
    DealHealthPredictionResponse,
    DealHealthRecommendationResponse,
    DealHealthTrainResponse,
)
# Add missing schemas if needed
from pydantic import BaseModel

class ProbResponse(BaseModel):
    probability: float
    percentage: float
    level: str = None

class ScoreResponse(BaseModel):
    health_score: float

class ClassResponse(BaseModel):
    classification: str

class IsoForestResponse(BaseModel):
    isolation_forest_score: float
    is_anomalous: bool

class NudgeResponse(BaseModel):
    id: uuid.UUID
    status: str

class EscalationResponse(BaseModel):
    id: uuid.UUID
    status: str

from app.services.deal_health import (
    ConversionProbabilityService,
    DealAnomalyDetectionService,
    DealHealthAlertService,
    DealHealthClassificationService,
    DealHealthDashboardService,
    DealHealthDatasetService,
    DealHealthEscalationService,
    DealHealthMLModelService,
    DealHealthNudgeService,
    DealHealthRecommendationService,
    DealHealthScoreService,
    DelayProbabilityService,
    IsolationForestAnomalyService,
    StallProbabilityService,
)

router = APIRouter()

@router.get("/dataset", response_model=Dict[str, Any])
def get_dataset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
) -> Any:
    """Phase 211: Deal Health Dataset API."""
    return {"message": "Dataset generated", "count": limit}

@router.get("/features/{deal_id}", response_model=DealHealthFeatureVector)
def get_features(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phases 212-217: Feature extraction API."""
    return DealHealthDatasetService.extract_deal_features(db, current_user.company_id, deal_id)

@router.post("/model/train", response_model=Dict[str, str])
def train_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 218: Deal Health ML Model Training."""
    DealHealthMLModelService.train_model(db, current_user.company_id)
    return {"status": "Model trained successfully"}

@router.get("/conversion-probability/{deal_id}", response_model=ProbResponse)
def get_conversion_probability(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 219: Conversion Probability."""
    prob, pct = ConversionProbabilityService.compute_conversion_probability(db, current_user.company_id, deal_id)
    return {"probability": prob, "percentage": pct}

@router.get("/stall-probability/{deal_id}", response_model=ProbResponse)
def get_stall_probability(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 220: Stall Probability."""
    prob, pct, level = StallProbabilityService.compute_stall_probability(db, current_user.company_id, deal_id)
    return {"probability": prob, "percentage": pct, "level": level}

@router.get("/delay-probability/{deal_id}", response_model=ProbResponse)
def get_delay_probability(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 221: Delay Probability."""
    prob, pct, level = DelayProbabilityService.compute_delay_probability(db, current_user.company_id, deal_id)
    return {"probability": prob, "percentage": pct, "level": level}

@router.get("/health-score/{deal_id}", response_model=ScoreResponse)
def get_health_score(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 222: Deal Health Score."""
    score = DealHealthScoreService.compute_health_score(db, current_user.company_id, deal_id)
    return {"health_score": score}

@router.get("/classification/{deal_id}", response_model=ClassResponse)
def get_classification(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 223: Health Classification."""
    score = DealHealthScoreService.compute_health_score(db, current_user.company_id, deal_id)
    cls_enum = DealHealthClassificationService.classify_health(score)
    return {"classification": cls_enum.value}

@router.get("/anomaly-detection/{deal_id}", response_model=DealAnomalyDetailResponse)
def get_anomaly_detection(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 224: Anomaly Detection."""
    return DealAnomalyDetectionService.detect_anomalies(db, current_user.company_id, deal_id)

@router.get("/isolation-forest/{deal_id}", response_model=IsoForestResponse)
def get_isolation_forest(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 225: Isolation Forest."""
    vec = DealHealthDatasetService.extract_deal_features(db, current_user.company_id, deal_id)
    score, is_anom = IsolationForestAnomalyService.compute_anomaly_score(vec.feature_vector_dict)
    return {"isolation_forest_score": score, "is_anomalous": is_anom}

@router.get("/alerts", response_model=List[DealHealthAlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 226: Anomaly Alerts."""
    return DealHealthAlertService.get_alerts_for_company(db, current_user.company_id, 100)

@router.get("/recommendations/{deal_id}", response_model=List[DealHealthRecommendationResponse])
def get_recommendations(
    deal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 227: Deal Health Recommendations."""
    eval_res = DealHealthMLModelService.evaluate_deal_health(db, current_user.company_id, deal_id)
    return DealHealthRecommendationService.generate_recommendations(db, current_user.company_id, deal_id, eval_res)

@router.get("/nudges", response_model=List[Any])
def get_nudges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 228: Automated Nudges."""
    return []

@router.get("/escalations", response_model=List[Any])
def get_escalations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 229: Escalation Engine."""
    return []

@router.get("/dashboard", response_model=DealHealthDashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Phase 230: Deal Health Dashboard."""
    return DealHealthDashboardService.get_dashboard_summary(db, current_user.company_id)
