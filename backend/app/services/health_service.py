"""
Loads the trained equipment health / RUL model
(ml_models/maintenance/train_health_model.py) and serves live predictions
for the current fleet. Mirrors forecast_service.py's pattern in the Energy
module: the model file + honest metrics are read once and cached, and every
prediction carries a confidence signal derived from the model's own
held-out accuracy rather than presenting every prediction as equally
trustworthy.
"""
import json
from datetime import timedelta
from pathlib import Path

import joblib
import pandas as pd

from app.utils.rul_features import add_engineered_features, top_contributing_factors

MODEL_DIR = Path(__file__).resolve().parents[2] / "ml_models" / "maintenance"
MODEL_PATH = MODEL_DIR / "health_rul_model.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"
SCATTER_PATH = MODEL_DIR / "prediction_scatter.json"


def get_prediction_scatter() -> dict:
    """Actual-vs-predicted RUL for the winning model, on all 100 NASA
    held-out test engines — same reliability diagnostic as the Energy
    forecast scatter."""
    if not SCATTER_PATH.exists():
        raise FileNotFoundError(
            f"No prediction scatter data at {SCATTER_PATH}. "
            "Run: python ml_models/maintenance/train_health_model.py"
        )
    return json.loads(SCATTER_PATH.read_text())

# Health-score status buckets (0-100 scale, derived from predicted RUL).
STATUS_THRESHOLDS = [
    (75, "Excellent"),
    (50, "Good"),
    (25, "Warning"),
    (0, "Critical"),
]

_cache = {}


def is_model_available() -> bool:
    return MODEL_PATH.exists()


def _load_model():
    if "model" not in _cache:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"No trained health model at {MODEL_PATH}. "
                "Run: python ml_models/maintenance/train_health_model.py"
            )
        _cache["model"] = joblib.load(MODEL_PATH)
    return _cache["model"]


def get_confidence() -> dict:
    if not METRICS_PATH.exists():
        return {"available": False}
    metrics = json.loads(METRICS_PATH.read_text())
    improvement = metrics["improvement_over_naive_pct"]
    if improvement >= 40:
        confidence = "high"
    elif improvement >= 15:
        confidence = "medium"
    else:
        confidence = "low"
    best = metrics["all_models"][metrics["best_model"]]
    return {
        "available": True,
        "model_used": metrics["best_model"],
        "mae_cycles": best["held_out_test_mae_cycles"],
        "r2": best["held_out_test_r2"],
        "improvement_over_naive_pct": improvement,
        "confidence": confidence,
    }


def rul_to_health_score(rul_cycles: float, clip: int = 125) -> float:
    return round(max(0.0, min(100.0, (rul_cycles / clip) * 100)), 1)


def health_score_to_status(health_score: float) -> str:
    for threshold, label in STATUS_THRESHOLDS:
        if health_score >= threshold:
            return label
    return "Critical"


def _build_features(asset_df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """asset_df = full reading history for ONE asset. Recomputes the exact
    same engineered features used at training time (shared with
    train_health_model.py via app.utils.rul_features, so the two paths
    can never silently drift apart), then returns just the latest row."""
    df = asset_df.copy()
    df["asset_id"] = "current"  # single-asset frame; group key is a no-op here
    df = add_engineered_features(df, "asset_id")
    latest = df.sort_values("cycle").iloc[[-1]]
    return latest[feature_cols]


def predict_asset_health(asset_df: pd.DataFrame) -> dict:
    """asset_df: reading history for one asset (>=1 row), ordered or not
    (sorted internally). Returns predicted RUL — with an honest 80%
    prediction interval, not just a point estimate — health score, status,
    predicted maintenance date, and model confidence."""
    bundle = _load_model()
    model, features, clip = bundle["model"], bundle["features"], bundle["rul_clip"]
    lo_model, hi_model = bundle.get("lo_model"), bundle.get("hi_model")

    X = _build_features(asset_df, features)
    predicted_rul = max(0.0, min(float(model.predict(X)[0]), clip))
    health_score = rul_to_health_score(predicted_rul, clip)
    status = health_score_to_status(health_score)

    rul_lower = rul_upper = None
    if lo_model is not None and hi_model is not None:
        lo = max(0.0, min(float(lo_model.predict(X)[0]), clip))
        hi = max(0.0, min(float(hi_model.predict(X)[0]), clip))
        rul_lower, rul_upper = round(min(lo, hi), 1), round(max(lo, hi), 1)

    factors = top_contributing_factors(
        X.iloc[0].to_dict(),
        bundle.get("feature_means", {}),
        bundle.get("feature_stds", {}),
        bundle.get("feature_importances") or {},
    )

    latest_row = asset_df.sort_values("cycle").iloc[-1]
    latest_timestamp = pd.to_datetime(latest_row["timestamp"])
    predicted_maintenance_date = latest_timestamp + timedelta(days=round(predicted_rul))
    maintenance_date_earliest = (
        latest_timestamp + timedelta(days=round(rul_lower)) if rul_lower is not None else None
    )
    maintenance_date_latest = (
        latest_timestamp + timedelta(days=round(rul_upper)) if rul_upper is not None else None
    )

    return {
        "predicted_rul_cycles": round(predicted_rul, 1),
        "rul_lower_cycles": rul_lower,
        "rul_upper_cycles": rul_upper,
        "health_score": health_score,
        "status": status,
        "latest_cycle": int(latest_row["cycle"]),
        "latest_timestamp": latest_timestamp,
        "predicted_maintenance_date": predicted_maintenance_date,
        "maintenance_date_earliest": maintenance_date_earliest,
        "maintenance_date_latest": maintenance_date_latest,
        "top_factors": factors,
        "confidence": get_confidence(),
    }
