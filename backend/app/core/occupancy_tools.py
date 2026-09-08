"""
Tools available to the Occupancy Agent's agentic investigation loop — same
pattern as app/core/maintenance_tools.py.
"""
from app.core.database import SessionLocal
from app.services import occupancy_service, security_service
from app.utils.occupancy_analytics import zone_status, building_summary, overcrowding_alerts


def _zone_meta(zone) -> dict:
    """Build the {zone_id, name, zone_type, capacity} meta dict for one Zone
    row. str() casts here silence Pylance's Column[str]-vs-str false
    positive for classic-style SQLAlchemy models — harmless at runtime,
    but keeps them in one place instead of scattered across every caller.
    """
    return {
        "zone_id": str(zone.zone_id),
        "name": str(zone.name),
        "zone_type": str(zone.zone_type),
        "capacity": zone.capacity,
    }


def _score_all_zones(db, building_id: str, only_restricted: bool = False) -> list[dict]:
    """Fetch every zone for a building, pull its readings, and run
    zone_status() on each — the shared core of get_building_occupancy_summary,
    get_overcrowded_zones, and get_restricted_zone_status.
    """
    zones = occupancy_service.list_zones(db, building_id)
    scored = []
    for z in zones:
        if only_restricted and str(z.zone_type) != "restricted":
            continue
        zone_id = str(z.zone_id)
        readings = occupancy_service.get_readings_df(db, zone_id, limit=500)
        scored.append(zone_status(_zone_meta(z), readings))
    return scored


def get_building_occupancy_summary(building_id: str = "BLD-HQ-01") -> dict:
    """Get building-wide occupancy: how many zones are monitored, total
    headcount, average utilization, and how many zones are currently
    overcrowded.

    Args:
        building_id: The building identifier, e.g. "BLD-HQ-01".
    """
    db = SessionLocal()
    try:
        scored = _score_all_zones(db, building_id)
        return building_summary(scored)
    finally:
        db.close()


def get_zone_status(zone_id: str) -> dict:
    """Get the current status for one specific zone: headcount, utilization
    percent, status bucket (Low/Moderate/Busy/Overcrowded), and today's peak.

    Args:
        zone_id: The zone identifier, e.g. "ZN-01".
    """
    db = SessionLocal()
    try:
        zone = occupancy_service.get_zone(db, zone_id)
        if not zone:
            return {"error": f"zone {zone_id} not found"}
        readings = occupancy_service.get_readings_df(db, str(zone.zone_id), limit=500)
        return zone_status(_zone_meta(zone), readings)
    finally:
        db.close()


def get_overcrowded_zones(building_id: str = "BLD-HQ-01") -> list[dict]:
    """Get all zones currently over the 90% utilization threshold, worth a
    closer look or a space-management action.

    Args:
        building_id: The building identifier, e.g. "BLD-HQ-01".
    """
    db = SessionLocal()
    try:
        scored = _score_all_zones(db, building_id)
        return overcrowding_alerts(scored)
    finally:
        db.close()


def get_restricted_zone_status(building_id: str = "BLD-HQ-01") -> list[dict]:
    """Get the current status of every RESTRICTED zone (e.g. server rooms)
    specifically — the zones worth checking for a Security handoff even
    when they're nowhere near the general overcrowding threshold, since a
    restricted zone showing ANY occupancy is unusual by definition.

    Args:
        building_id: The building identifier, e.g. "BLD-HQ-01".
    """
    db = SessionLocal()
    try:
        return _score_all_zones(db, building_id, only_restricted=True)
    finally:
        db.close()


def flag_restricted_zone_for_security_review(zone_id: str, reason: str, severity: str = "medium") -> dict:
    """Hand off a restricted-zone occupancy concern to the Security Agent by
    opening a real security alert. Use this ONLY for zone_type='restricted'
    zones showing occupancy that badge-log cross-reference should verify —
    occupancy sensing alone can't confirm WHO is present.

    Args:
        zone_id: The restricted zone's identifier, e.g. "ZN-07".
        reason: A concise explanation of what was observed and why it warrants security review.
        severity: One of "low", "medium", "high".
    """
    db = SessionLocal()
    try:
        return security_service.open_alert(
            db, alert_type="restricted_zone_occupancy", description=reason,
            severity=severity, source="occupancy_agent", zone_id=zone_id,
        )
    finally:
        db.close()


ALL_TOOLS = [
    get_building_occupancy_summary,
    get_zone_status,
    get_overcrowded_zones,
    get_restricted_zone_status,
    flag_restricted_zone_for_security_review,
]