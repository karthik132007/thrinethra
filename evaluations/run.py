"""Reproducible synthetic baseline benchmark. This is NOT real-world safety validation."""

import json
import math
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.intelligence.analytics import Analytics
from packages.forecasting.baseline import forecast
from packages.correlation.graph import correlate


def metrics(pred, true):
    pred = np.asarray(pred, bool)
    true = np.asarray(true, bool)
    tp = int(np.sum(pred & true))
    fp = int(np.sum(pred & ~true))
    fn = int(np.sum(~pred & true))
    return {
        "precision": round(tp / max(tp + fp, 1), 4),
        "recall": round(tp / max(tp + fn, 1), 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "false_alert_samples": fp,
    }


def main():
    start = time.perf_counter()
    rng = np.random.default_rng(42)
    zone = {
        "id": "benchmark",
        "capacity": 40,
        "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "restricted": False,
    }
    single = []
    temporal = []
    truth = []
    latencies = []
    for trial in range(20):
        analytics = Analytics()
        first = None
        for t in range(150):
            count = 12 + int(rng.integers(-2, 3))
            if t in (10, 25, 40):
                count = 50
            if 65 <= t < 110:
                count = 48 + int(rng.integers(-2, 3))
            objects = [
                {
                    "id": i,
                    "class": "person",
                    "center": [0.15 + (i % 8) * 0.08, 0.2 + (i // 8) * 0.09],
                    "confidence": 0.9,
                    "speed": 0.01,
                    "velocity": [0.01, 0],
                }
                for i in range(count)
            ]
            _, signals = analytics.analyze("benchmark-camera", zone, objects, float(t))
            detected = any(s["type"] == "potential_crowd_safety_risk" for s in signals)
            single.append(count >= 32)
            temporal.append(detected)
            truth.append(71 <= t < 110)
            if detected and 65 <= t < 110 and first is None:
                first = t - 65
        if first is not None:
            latencies.append(first)
    errors = {
        "last_value": [],
        "moving_average": [],
        "exponential_smoothing": [],
        "rolling_regression": [],
    }
    for trial in range(40):
        time_values = np.arange(180)
        counts = np.maximum(
            0,
            20
            + time_values * 0.18
            + 5 * np.sin(time_values / 24)
            + rng.normal(0, 1.3, 180),
        )
        for cut in range(30, 160, 10):
            history = [
                {"timestamp": float(t), "count": float(counts[t])}
                for t in range(cut - 30, cut)
            ]
            actual = float(counts[cut + 9])
            predictions = forecast(history, 60, horizon=10)
            smooth = history[0]["count"]
            for row in history[1:]:
                smooth = 0.3 * row["count"] + 0.7 * smooth
            expected = {
                "last_value": history[-1]["count"],
                "moving_average": float(np.mean(counts[cut - 5 : cut])),
                "exponential_smoothing": smooth,
                "rolling_regression": predictions["points"][-1]["value"],
            }
            for method, value in expected.items():
                errors[method].append(value - actual)
    forecasting = {
        key: {
            "mae": round(float(np.mean(np.abs(values))), 3),
            "rmse": round(float(np.sqrt(np.mean(np.square(values)))), 3),
            "samples": len(values),
        }
        for key, values in errors.items()
    }
    a = {
        "camera_id": "a",
        "started_at": 100,
        "type": "potential_crowd_safety_risk",
        "provenance": "synthetic",
    }
    cases = [
        (a | {"camera_id": "b", "started_at": 110}, True),
        (a | {"camera_id": "b", "started_at": 210}, True),
        (a | {"camera_id": "c", "started_at": 110}, False),
        (a | {"camera_id": "b", "started_at": 300}, False),
        (a | {"camera_id": "b", "type": "traffic_obstruction"}, False),
        (a | {"camera_id": "b", "provenance": "video_inference"}, False),
    ]
    cp = [bool(correlate(a, b, {frozenset(("a", "b"))})) for b, _ in cases]
    ct = [label for _, label in cases]
    data = {
        "seed": 42,
        "provenance": "synthetic benchmark; detector bypassed",
        "event_evaluation_unit": "Per-second samples across 20 constructed episodes; positive label begins after 6 seconds of sustained high occupancy",
        "event_samples": len(truth),
        "single_frame_threshold": metrics(single, truth),
        "temporal_crowd_baseline": metrics(temporal, truth),
        "mean_detection_delay_from_sustained_onset_seconds": round(
            float(np.mean(latencies)), 2
        ),
        "forecast_horizon_seconds": 10,
        "forecasting": forecasting,
        "correlation_labeled_pairs": len(cases),
        "correlation": metrics(cp, ct),
        "not_evaluated": [
            "Detection mAP",
            "Real crowd counting MAE",
            "Natural-video event precision/recall",
            "Real-world forecast lead time",
            "Calibrated uncertainty coverage",
            "General-purpose LLM accuracy",
        ],
        "runtime_seconds": round(time.perf_counter() - start, 3),
    }
    (ROOT / "evaluations/results.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
