"""Correlates aggregate events, never people or tracking identities."""

import math


def correlate(a, b, connections, window=120):
    if a["camera_id"] == b["camera_id"] or a["provenance"] != b["provenance"]:
        return None
    connected = frozenset((a["camera_id"], b["camera_id"])) in connections
    delta = abs(a["started_at"] - b["started_at"])
    crowd = lambda event: any(
        value in event["type"] for value in ("crowd", "bottleneck")
    )
    if not connected or delta > window or crowd(a) != crowd(b):
        return None
    reasons = [
        "Connected camera zones",
        "compatible aggregate event types",
        f"onset timestamps {delta:.1f}s apart",
    ]
    confidence = 0.6 + 0.2 * (1 - delta / window)
    if all(key in record for record in (a, b) for key in ("lat", "lon")):
        lat = math.radians((a["lat"] + b["lat"]) / 2)
        distance = math.hypot(
            (a["lat"] - b["lat"]) * 111_195,
            (a["lon"] - b["lon"]) * 111_195 * math.cos(lat),
        )
        if distance > 2000:
            return None
        reasons.append(f"camera proximity {distance:.0f}m")
    if (
        a.get("mean_speed", 0) > 0.015
        and b.get("mean_speed", 0) > 0.015
        and "direction" in a
        and "direction" in b
    ):
        angle = abs((a["direction"] - b["direction"] + 180) % 360 - 180)
        reasons.append(f"aggregate flow directions differ by {angle:.0f}°")
        confidence += 0.05 if angle < 60 else -0.05
    return {
        "confidence": round(min(0.95, confidence), 3),
        "explanation": "; ".join(reasons)
        + ". Shared regional conditions are possible; no identity matching performed.",
    }
