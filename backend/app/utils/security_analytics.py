"""
Security analytics: runs the trained Isolation Forest (see
ml_models/security/train_anomaly_model.py) against the current event
stream, and rolls the result up into building-wide KPIs. Also exposes the
model's own honest offline evaluation (precision/recall/F1 against injected
synthetic ground truth) so the dashboard can show real confidence, not a
claimed one.
"""
import json
from pathlib import Path

import joblib
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models" / "security"
MODEL_PATH = MODEL_DIR / "anomaly_model.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"

RISK_ENCODE = {"low": 0, "medium": 1, "high": 2}
_bundle_cache = None


def _load_model():
    global _bundle_cache
    if _bundle_cache is None:
        _bundle_cache = joblib.load(MODEL_PATH)
    return _bundle_cache


def is_model_available() -> bool:
    return MODEL_PATH.exists()


def get_model_confidence() -> dict:
    if not METRICS_PATH.exists():
        return {"available": False}
    m = json.loads(METRICS_PATH.read_text())
    return {
        "available": True,
        "model_used": m.get("model"),
        "precision": m.get("precision"),
        "recall": m.get("recall"),
        "f1": m.get("f1"),
        "note": m.get("note"),
    }


def _engineer_features(events_df: pd.DataFrame, first_visit_map: dict | None = None) -> pd.DataFrame:
    df = events_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["hour_of_day"] = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60
    df["is_business_hours"] = ((df["hour_of_day"] >= 8.5) & (df["hour_of_day"] <= 18.5) & (df["timestamp"].dt.dayofweek < 5)).astype(int)
    df["is_weekend"] = (df["timestamp"].dt.dayofweek >= 5).astype(int)
    df["risk_level_enc"] = df["risk_level"].map(RISK_ENCODE).fillna(0)
    df["access_denied"] = (~df["access_granted"]).astype(int)
    df["recent_denials_by_employee"] = (
        df.groupby("employee_id")["access_denied"]
        .transform(lambda s: s.rolling(10, min_periods=1).sum())
    )
    # Same novelty feature as training (see ml_models/security/train_anomaly_model.py) —
    # has this employee ever used this access point before? When a
    # first_visit_map (from the FULL event history, not just this scored
    # window) is supplied, use the true first-visit timestamp; otherwise
    # fall back to novelty-within-this-window only (used during offline
    # training, where the whole dataset IS the window).
    if first_visit_map is not None:
        df["_first_visit_ts"] = df.apply(
            lambda r: first_visit_map.get((r["employee_id"], r["access_point_id"])), axis=1
        )
        df["is_novel_access_point_for_employee"] = (df["timestamp"] <= df["_first_visit_ts"]).astype(int)
        df = df.drop(columns=["_first_visit_ts"])
    else:
        df["_visit_number"] = df.groupby(["employee_id", "access_point_id"]).cumcount()
        df["is_novel_access_point_for_employee"] = (df["_visit_number"] == 0).astype(int)
        df = df.drop(columns=["_visit_number"])
    return df


def score_events(events_df: pd.DataFrame, first_visit_map: dict | None = None) -> pd.DataFrame:
    """Runs the live Isolation Forest against the given events and adds
    `flagged` (bool) + `anomaly_score` (higher = more anomalous) columns.
    Pass first_visit_map (see security_service.get_first_visit_timestamps)
    for an accurate novelty feature against full history rather than just
    this scored window."""
    if events_df.empty:
        return events_df
    bundle = _load_model()
    model, features = bundle["model"], bundle["features"]
    engineered = _engineer_features(events_df, first_visit_map)
    X = engineered[features]
    raw_pred = model.predict(X)
    scores = -model.score_samples(X)  # flip sign: higher = more anomalous, easier to reason about
    engineered["flagged"] = raw_pred == -1
    engineered["anomaly_score"] = scores.round(3)
    return engineered


def building_security_summary(scored_events: pd.DataFrame, access_points: list[dict]) -> dict:
    if scored_events.empty:
        return {
            "access_points_monitored": len(access_points), "events_last_24h": 0,
            "denied_last_24h": 0, "flagged_last_24h": 0,
        }
    cutoff = scored_events["timestamp"].max() - pd.Timedelta(hours=24)
    recent = scored_events[scored_events["timestamp"] >= cutoff]
    return {
        "access_points_monitored": len(access_points),
        "events_last_24h": int(len(recent)),
        "denied_last_24h": int((~recent["access_granted"]).sum()),
        "flagged_last_24h": int(recent["flagged"].sum()) if "flagged" in recent else 0,
    }


def top_flagged_events(scored_events: pd.DataFrame, limit: int = 15) -> list[dict]:
    if scored_events.empty or "flagged" not in scored_events:
        return []
    flagged = scored_events[scored_events["flagged"]].sort_values("anomaly_score", ascending=False).head(limit)
    return [{
        "event_id": r.event_id,
        "access_point_id": r.access_point_id,
        "employee_id": r.employee_id,
        "timestamp": r.timestamp,
        "access_granted": bool(r.access_granted),
        "risk_level": r.risk_level,
        "anomaly_score": float(r.anomaly_score),
    } for r in flagged.itertuples(index=False)]
