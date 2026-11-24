"""Interpretable temporal baselines, with experimental thresholds and no accident confirmation."""

from collections import deque
import math
import numpy as np

DEFAULTS = {
    "persistence_seconds": 6,
    "occupancy_threshold": 0.8,
    "stationary_seconds": 8,
    "forecast_horizon": 60,
    "risk_high": 50,
    "risk_critical": 75,
    "cooldown_seconds": 30,
    "confidence_threshold": 0.3,
}


def inside(point, polygon):
    x, y = point
    result = False
    for i in range(len(polygon)):
        ax, ay = polygon[i - 1]
        bx, by = polygon[i]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            result = not result
    return result


class Analytics:
    def __init__(self):
        self.history = {}
        self.since = {}
        self.stationary = {}
        self.abrupt = {}

    def analyze(self, camera_id, zone, tracks, timestamp, config=None, kind="crowd"):
        cfg = DEFAULTS | (config or {})
        selected = [t for t in tracks if inside(t["center"], zone["polygon"])]
        people = [t for t in selected if t["class"] == "person"]
        vehicles = [t for t in selected if t["class"] != "person"]
        population = vehicles if kind == "road" else people
        count = len(population)
        ratio = count / max(zone["capacity"], 1)
        speeds = [t["speed"] for t in population]
        speed = float(np.mean(speeds)) if speeds else 0
        confidence = (
            float(np.mean([t["confidence"] for t in population])) if population else 0
        )
        history = self.history.setdefault(zone["id"], deque(maxlen=120))
        history.append((timestamp, count, speed))
        smooth = float(np.mean([v[1] for v in list(history)[-5:]]))
        elapsed = timestamp - history[0][0]
        growth = (smooth - history[0][1]) / max(elapsed, 1)
        moving = [t for t in population if t["speed"] > 0.015]
        mean_v = np.mean([t["velocity"] for t in moving], axis=0) if moving else [0, 0]
        coherence = (
            float(
                math.hypot(*mean_v) / max(np.mean([t["speed"] for t in moving]), 0.001)
            )
            if moving
            else 1
        )
        conflict = round(1 - min(coherence, 1), 3)
        concentration = 0
        if population:
            cells = {}
            for t in population:
                key = (int(t["center"][0] * 4), int(t["center"][1] * 4))
                cells[key] = cells.get(key, 0) + 1
            concentration = max(cells.values()) / count
        metric = {
            "count": count,
            "people": len(people),
            "vehicles": len(vehicles),
            "occupancy": round(ratio, 3),
            "smoothed_count": round(smooth, 2),
            "mean_speed": round(speed, 4),
            "growth_rate": round(growth, 3),
            "direction": round(math.degrees(math.atan2(mean_v[1], mean_v[0])), 1),
            "conflicting_flow": conflict,
            "concentration": round(concentration, 3),
            "confidence": round(confidence, 3),
            "tracks": tracks,
        }
        conditions = {}
        if kind == "crowd":
            conditions["potential_crowd_safety_risk"] = (
                smooth / max(zone["capacity"], 1) >= cfg["occupancy_threshold"],
                [
                    f"Smoothed occupancy {smooth:.1f}/{zone['capacity']}",
                    f"Image-plane movement {speed:.3f} frame-widths/s",
                    f"Occupancy growth {growth:.2f} objects/s",
                    f"Conflicting flow {conflict:.2f}",
                ],
            )
            conditions["bottleneck"] = (
                ratio > 0.55 and speed < 0.015 and concentration > 0.25,
                [
                    f"Spatial concentration {concentration:.2f}",
                    f"Reduced image-plane movement {speed:.3f}/s",
                ],
            )
            conditions["sudden_crowd_movement"] = (
                len(people) >= 5 and speed > 0.14,
                [f"Mean image-plane movement {speed:.3f}/s"],
            )
        else:
            present = set()
            stopped = []
            for track in vehicles:
                key = (camera_id, zone["id"], track["id"])
                present.add(key)
                if track["speed"] < 0.008:
                    self.stationary.setdefault(key, timestamp)
                    if timestamp - self.stationary[key] >= cfg["stationary_seconds"]:
                        stopped.append(track)
                else:
                    self.stationary.pop(key, None)
            for key in list(self.stationary):
                if key[:2] == (camera_id, zone["id"]) and key not in present:
                    self.stationary.pop(key)
            conditions[
                "restricted_zone_stop"
                if zone.get("restricted")
                else "traffic_obstruction"
            ] = (
                bool(stopped),
                [
                    f"{len(stopped)} vehicle tracks stationary for ≥{cfg['stationary_seconds']} seconds"
                ],
            )
            conditions["abnormal_traffic_congestion"] = (
                ratio > 0.65 and speed < 0.02,
                [
                    f"Vehicle occupancy {ratio:.0%}",
                    f"Mean image-plane movement {speed:.3f}/s",
                ],
            )
            for track in vehicles:
                if track.get("sudden_stop"):
                    self.abrupt[(zone["id"], track["id"])] = timestamp
            for key, seen in list(self.abrupt.items()):
                if timestamp - seen > 12:
                    self.abrupt.pop(key, None)
            abrupt = [t for t in vehicles if (zone["id"], t["id"]) in self.abrupt]
            # Multi-signal, trajectory-based hypothesis; box overlap is deliberately unused.
            conditions["suspected_road_incident"] = (
                len(abrupt) >= 2 and ratio > 0.3 and speed < 0.025,
                [
                    f"{len(abrupt)} recent trajectory decelerations (12s window)",
                    f"{count} vehicles in zone",
                    f"Reduced post-change movement {speed:.3f}/s",
                ],
            )
        signals = []
        for type_, (condition, factors) in conditions.items():
            key = (zone["id"], type_)
            if condition and confidence >= cfg["confidence_threshold"]:
                self.since.setdefault(key, timestamp)
                duration = timestamp - self.since[key]
                if duration >= cfg["persistence_seconds"]:
                    signals.append(
                        {
                            "type": type_,
                            "confidence": round(min(confidence, 0.95), 3),
                            "factors": factors
                            + [f"Condition persisted {duration:.1f}s"],
                            "duration": duration,
                            "tracks": [t["id"] for t in population],
                        }
                    )
            else:
                self.since.pop(key, None)
        metric["persistence"] = max([s["duration"] for s in signals], default=0)
        return metric, signals


def risk_score(metric, forecast, correlated=0, config=None):
    cfg = DEFAULTS | (config or {})
    components = {
        "occupancy": min(35, metric["occupancy"] * 30),
        "persistence": min(15, metric.get("persistence", 0) / 2),
        "growth": min(10, max(0, metric["growth_rate"]) * 8),
        "reduced_movement": 10
        if metric["occupancy"] > 0.5 and metric["mean_speed"] < 0.02
        else 0,
        "forecast": min(20, max(0, forecast.get("peak_ratio", 0) - 0.6) * 25),
        "nearby_incidents": min(10, correlated * 5),
    }
    # Severity and confidence are reported separately; low confidence limits evidence strength.
    score = round(min(100, sum(components.values())), 1)
    level = (
        "critical"
        if score >= cfg["risk_critical"]
        else "high"
        if score >= cfg["risk_high"]
        else "elevated"
        if score >= 25
        else "normal"
    )
    return {
        "score": score,
        "level": level,
        "confidence": metric["confidence"],
        "components": {k: round(v, 2) for k, v in components.items()},
        "explanation": "Experimental weighted score from occupancy, persistence, growth, movement, forecast and connected incidents.",
    }
