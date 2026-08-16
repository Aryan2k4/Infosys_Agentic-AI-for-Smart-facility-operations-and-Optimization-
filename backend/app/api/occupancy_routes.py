from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.intelligence_engine import investigate_occupancy
from app.services import occupancy_service
from app.agents.occupancy_agent import OccupancyAgent
from app.utils.occupancy_analytics import get_model_confidence

router = APIRouter(prefix="/occupancy", tags=["occupancy"])

DEFAULT_BUILDING = "BLD-HQ-01"


@router.post("/ingest")
def ingest(db: Session = Depends(get_db)):
    """Milestone 3: integrate occupancy monitoring data. See
    data/build_occupancy_dataset.py for the real UCI Occupancy Detection
    source and the disclosed synthetic multi-zone projection."""
    try:
        result = occupancy_service.ingest_zones(db)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    return {"status": "ok", "building_id": DEFAULT_BUILDING, **result}


@router.get("/building")
def building(building_id: str = Query(DEFAULT_BUILDING), db: Session = Depends(get_db)):
    """Single call that powers the occupancy dashboard: building summary,
    all scored zones, heatmap data, and top alerts."""
    agent = OccupancyAgent(db, building_id)
    result = agent.run()
    analysis = result["analysis"]
    return {
        "building_id": building_id,
        "building": analysis["building"],
        "zones": analysis["zones"],
        "heatmap": analysis["heatmap"],
        "top_alerts": result["recommendations"][:8],
        "model_confidence": get_model_confidence(),
    }


@router.get("/zones")
def zones(building_id: str = Query(DEFAULT_BUILDING), db: Session = Depends(get_db)):
    agent = OccupancyAgent(db, building_id)
    analysis = agent.analyze()
    return {"building_id": building_id, "zones": analysis["zones"]}


@router.get("/zones/{zone_id}")
def zone_detail(zone_id: str, db: Session = Depends(get_db)):
    zone = occupancy_service.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(404, f"Zone {zone_id} not found")
    readings = occupancy_service.get_readings_df(db, zone_id)
    if readings.empty:
        raise HTTPException(404, f"No readings for zone {zone_id}")
    from app.utils.occupancy_analytics import zone_status
    meta = {"zone_id": zone.zone_id, "name": zone.name, "zone_type": zone.zone_type, "capacity": zone.capacity}
    return zone_status(meta, readings)


@router.get("/zones/{zone_id}/history")
def zone_history(zone_id: str, limit: int = Query(200, le=1000), db: Session = Depends(get_db)):
    """Raw headcount history for a zone (for the utilization trend chart)."""
    readings = occupancy_service.get_readings_df(db, zone_id, limit=limit)
    if readings.empty:
        raise HTTPException(404, f"No readings for zone {zone_id}")
    return {"zone_id": zone_id, "readings": readings.to_dict(orient="records")}


@router.get("/alerts")
def alerts(building_id: str = Query(DEFAULT_BUILDING), db: Session = Depends(get_db)):
    agent = OccupancyAgent(db, building_id)
    return {"building_id": building_id, "alerts": agent.recommend()}


@router.get("/investigate")
def investigate(building_id: str = Query(DEFAULT_BUILDING)):
    """Genuinely agentic endpoint: the model decides which zones to
    inspect and whether a restricted zone's occupancy warrants a real
    handoff to the Security Agent."""
    return investigate_occupancy(building_id)
