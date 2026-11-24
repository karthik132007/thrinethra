import math
import numpy as np
from packages.intelligence.analytics import Analytics, inside, risk_score
from packages.tracking.features import Trajectories
from packages.forecasting.baseline import forecast
from packages.correlation.graph import correlate
from demo.scenario import Scenario

ZONE = {
    "id": "z",
    "capacity": 10,
    "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
    "restricted": False,
}


def tracks(count=12, speed=0, cls="person"):
    return [
        {
            "id": i,
            "class": cls,
            "center": [0.3 + i * 0.01, 0.5],
            "confidence": 0.9,
            "speed": speed,
            "velocity": [speed, 0],
            "sudden_stop": False,
        }
        for i in range(count)
    ]


def test_roi_polygon():
    assert inside([0.5, 0.5], ZONE["polygon"])
    assert not inside([1.2, 0.5], ZONE["polygon"])


def test_temporal_threshold_suppresses_single_frame():
    analytics = Analytics()
    _, signals = analytics.analyze("c", ZONE, tracks(), 100)
    assert not signals
    for t in range(101, 108):
        metric, signals = analytics.analyze("c", ZONE, tracks(), t)
    assert any(s["type"] == "potential_crowd_safety_risk" for s in signals)
    assert metric["occupancy"] == 1.2


def test_condition_reset_prevents_accumulated_spikes():
    analytics = Analytics()
    for t in range(20):
        _, signals = analytics.analyze("c", ZONE, tracks() if t % 2 else [], t)
        assert not signals


def test_stationary_vehicle_temporal_evidence():
    analytics = Analytics()
    for t in range(20):
        _, signals = analytics.analyze("c", ZONE, tracks(5, 0, "car"), t, kind="road")
    assert any(s["type"] == "traffic_obstruction" for s in signals)
    assert not any(s["type"] == "suspected_road_incident" for s in signals)


def test_road_collision_hypothesis_needs_multiple_signals():
    analytics = Analytics()
    objects = tracks(5, 0.01, "car")
    for o in objects[:2]:
        o["sudden_stop"] = True
    for t in range(10):
        _, signals = analytics.analyze("c", ZONE, objects, t, kind="road")
        for o in objects:
            o["sudden_stop"] = False
    assert any(s["type"] == "suspected_road_incident" for s in signals)


def test_anonymous_tracks_expire_and_motion_units():
    tracker = Trajectories(ttl=3)

    def detection(x):
        return [
            {
                "id": 1,
                "class": "person",
                "bbox": [x, 0.2, x + 0.1, 0.6],
                "confidence": 0.9,
            }
        ]

    tracker.update(detection(0.1), 1)
    row = tracker.update(detection(0.2), 2)[0]
    assert math.isclose(row["speed"], 0.1)
    assert row["dwell"] == 1
    tracker.update([], 6)
    assert not tracker.history


def test_forecast_recovers_linear_signal_and_interval():
    result = forecast(
        [{"timestamp": i, "count": 10 + 2 * i} for i in range(20)], 60, 30
    )
    assert result["ready"]
    assert result["slope"] == 2
    assert result["points"][-1]["value"] == 108
    assert result["threshold_crossing_seconds"] == 6
    assert all(p["lower"] <= p["value"] <= p["upper"] for p in result["points"])
    assert not forecast([], 10)["ready"]


def test_correlation_requires_connectivity_time_and_same_provenance():
    a = {
        "camera_id": "a",
        "started_at": 100,
        "type": "potential_crowd_safety_risk",
        "provenance": "synthetic",
    }
    b = a | {"camera_id": "b", "started_at": 110}
    assert correlate(a, b, {frozenset(("a", "b"))})
    assert not correlate(a, b, set())
    assert not correlate(
        a, b | {"provenance": "video_inference"}, {frozenset(("a", "b"))}
    )
    assert not correlate(a, b | {"started_at": 500}, {frozenset(("a", "b"))})


def test_risk_bounds_separates_confidence():
    metric = {
        "occupancy": 2,
        "persistence": 100,
        "growth_rate": 10,
        "mean_speed": 0,
        "confidence": 0.3,
    }
    result = risk_score(metric, {"peak_ratio": 5}, 10)
    assert 0 <= result["score"] <= 100
    assert result["confidence"] == 0.3
    assert result["components"]
    assert result["explanation"]


def test_correlation_rejects_distant_connected_cameras():
    a = {
        "camera_id": "a",
        "started_at": 100,
        "type": "bottleneck",
        "provenance": "synthetic",
        "lat": 17.0,
        "lon": 81.0,
    }
    b = a | {"camera_id": "b", "lat": 18.0}
    assert not correlate(a, b, {frozenset(("a", "b"))})
