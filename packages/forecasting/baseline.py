"""Observation-driven forecasting with rolling validation of three interpretable baselines."""

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
    times = np.array([r["timestamp"] for r in rows], float)
    y = np.array([r["count"] for r in rows], float)
    x = times - times[-1]
    observed_slope, intercept = (
        np.polyfit(x, y, 1) if np.ptp(x) > 0 else (0, float(np.mean(y)))
    )
    smooth = y[0]
    for value in y[1:]:
        smooth = 0.3 * value + 0.7 * smooth
    errors = {
        "rolling linear regression": [],
        "last observation": [],
        "exponential smoothing": [],
    }
    for cut in range(5, len(y)):
        xx = times[:cut] - times[cut - 1]
        yy = y[:cut]
        a, b = np.polyfit(xx, yy, 1) if np.ptp(xx) > 0 else (0, yy[-1])
        ema = yy[0]
        for value in yy[1:]:
            ema = 0.3 * value + 0.7 * ema
        candidates = {
            "rolling linear regression": max(0, a * (times[cut] - times[cut - 1]) + b),
            "last observation": yy[-1],
            "exponential smoothing": ema,
        }
        for name, prediction in candidates.items():
            errors[name].append(float(prediction - y[cut]))
    scores = {
        name: round(float(np.mean(np.abs(values))), 4)
        for name, values in errors.items()
        if values
    }
    # Short windows retain regression until there is enough temporal validation evidence.
    method = (
        min(scores, key=scores.get) if len(y) >= 15 else "rolling linear regression"
    )
    slope = float(observed_slope) if method == "rolling linear regression" else 0.0
    base = (
        float(intercept)
        if method == "rolling linear regression"
        else float(y[-1])
        if method == "last observation"
        else float(smooth)
    )
    selected_errors = errors[method]
    fitted = observed_slope * x + intercept
    residual = (
        float(np.sqrt(np.mean(np.square(selected_errors))))
        if selected_errors
        else float(np.sqrt(np.mean((y - fitted) ** 2)))
    )
    dt = float(np.median(np.diff(times))) if len(times) > 1 else 1.0
    dt = max(dt, 0.01)
    sxx = max(float(np.sum((x - x.mean()) ** 2)), 0.001)
    points = []
    for step in np.linspace(horizon / 12, horizon, 12):
        prediction = max(0, base + slope * step)
        scale = (
            np.sqrt(1 + 1 / len(y) + (step - x.mean()) ** 2 / sxx)
            if method == "rolling linear regression"
            else np.sqrt(1 + step / (dt * len(y)))
        )
        uncertainty = 1.96 * max(residual, 0.5) * scale
        points.append(
            {
                "timestamp": float(times[-1] + step),
                "value": round(prediction, 2),
                "lower": round(max(0, prediction - uncertainty), 2),
                "upper": round(prediction + uncertainty, 2),
            }
        )
    crossing = (
        (capacity - base) / slope if slope > 0 else (0 if base >= capacity else None)
    )
    return {
        "ready": True,
        "method": method,
        "horizon": horizon,
        "points": points,
        "slope": round(slope, 4),
        "observed_trend": round(float(observed_slope), 4),
        "residual_rmse": round(residual, 3),
        "capacity": capacity,
        "peak_ratio": max(p["value"] for p in points) / max(capacity, 1),
        "threshold_crossing_seconds": round(max(0, float(crossing)), 1)
        if crossing is not None and crossing <= horizon
        else None,
        "backtest_mae": scores,
        "validation": "Rolling one-step errors on recent observations; models are selected locally, not validated safety predictors.",
        "uncertainty": "Approximate residual-based interval; coverage is not calibrated for public safety.",
        "factors": [
            f"Selected {method} using recent temporal validation",
            f"Observed trend {observed_slope:.3f} objects/s",
            f"{len(y)} measured observations",
        ],
    }
