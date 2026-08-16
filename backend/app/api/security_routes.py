from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.intelligence_engine import investigate_security
from app.services import security_service
from app.agents.security_agent import SecurityAgent
from app.utils.security_analytics import get_model_confidence

router = APIRouter(prefix="/security", tags=["security"])

DEFAULT_BUILDING = "BLD-HQ-01"


@router.post("/ingest")
def ingest(db: Session = Depends(get_db)):
    """Milestone 3: integrate access-control monitoring data. See
    data/build_security_dataset.py for the full honesty disclosure — this
    is a synthetic-but-disclosed dataset with injected labeled anomalies."""
    try:
        result = security_service.ingest_events(db)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    return {"status": "ok", "building_id": DEFAULT_BUILDING, **result}


@router.get("/building")
def building(building_id: str = Query(DEFAULT_BUILDING), db: Session = Depends(get_db)):
    """Single call that powers the security dashboard: building summary,
    flagged events, access points, and top alerts."""
    agent = SecurityAgent(db, building_id)
    result = agent.run()
    analysis = result["analysis"]
    return {
        "building_id": building_id,
        "building": analysis["building"],
        "flagged_events": analysis["flagged_events"],
        "access_points": analysis["access_points"],
        "top_alerts": result["recommendations"][:8],
        "model_confidence": get_model_confidence(),
    }


@router.get("/access-points")
def access_points(building_id: str = Query(DEFAULT_BUILDING), db: Session = Depends(get_db)):
    aps = security_service.list_access_points(db, building_id)
    return {
        "building_id": building_id,
        "access_points": [{"access_point_id": a.access_point_id, "name": a.name, "zone_id": a.zone_id, "risk_level": a.risk_level} for a in aps],
    }


@router.get("/events")
def events(limit: int = Query(200, le=1000), db: Session = Depends(get_db)):
    """Recent raw access events (for the access timeline)."""
    df = security_service.get_recent_events_df(db, limit=limit)
    if df.empty:
        return {"events": []}
    return {"events": df.drop(columns=["is_anomaly_ground_truth", "anomaly_type_ground_truth"], errors="ignore").to_dict(orient="records")}


@router.get("/alerts")
def alerts(building_id: str = Query(DEFAULT_BUILDING), status: str | None = Query(None), db: Session = Depends(get_db)):
    """All security alerts, including ones created via the Occupancy
    Agent's cross-agent handoff (source='occupancy_agent')."""
    return {"building_id": building_id, "alerts": security_service.list_alerts(db, building_id, status)}


@router.get("/investigate")
def investigate(building_id: str = Query(DEFAULT_BUILDING)):
    """Genuinely agentic endpoint: the model decides which flagged events
    warrant a real alert, weighing anomaly score against access-point risk."""
    return investigate_security(building_id)
