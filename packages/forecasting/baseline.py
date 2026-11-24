"""Rolling linear regression compared to last-value and moving-average baselines."""

import numpy as np


def forecast(history, capacity, horizon=60):
    if len(history) < 5:
        return {
            "ready": False,
            "reason": "At least five observations required",
            "points": [],
            "horizon": horizon,
            "peak_ratio": 0,
        }
    rows = history[-60:]
    times = np.array([r["timestamp"] for r in rows])
    y = np.array([r["count"] for r in rows], dtype=float)
    x = times - times[-1]
    slope, intercept = np.polyfit(x, y, 1) if np.ptp(x) > 0 else (0, float(np.mean(y)))
    fitted = slope * x + intercept
    residual = float(np.sqrt(np.mean((y - fitted) ** 2)))
    steps = np.linspace(horizon / 12, horizon, 12)
    points = []
    sxx = max(float(np.sum((x - x.mean()) ** 2)), 0.001)
    for step in steps:
        prediction = max(0, float(intercept + slope * step))
        uncertainty = (
            1.96
            * max(residual, 0.5)
            * np.sqrt(1 + 1 / len(y) + (step - x.mean()) ** 2 / sxx)
        )
        points.append(
            {
                "timestamp": float(times[-1] + step),
                "value": round(prediction, 2),
                "lower": round(max(0, prediction - uncertainty), 2),
                "upper": round(prediction + uncertainty, 2),
            }
        )
    crossing = (capacity - intercept) / slope if slope > 0 else None
    return {
        "ready": True,
        "method": "rolling linear regression",
        "horizon": horizon,
        "points": points,
        "slope": round(float(slope), 4),
        "residual_rmse": round(residual, 3),
        "capacity": capacity,
        "peak_ratio": max(p["value"] for p in points) / max(capacity, 1),
        "threshold_crossing_seconds": round(max(0, float(crossing)), 1)
        if crossing is not None and crossing <= horizon
        else None,
        "uncertainty": "Approximate 95% residual-based prediction interval; not calibrated for crowd safety.",
        "factors": [
            f"Rolling trend {slope:.3f} objects/s",
            f"{len(y)} recent observations",
        ],
    }
