"""Seeded synthetic trajectory generator; generated frames are never called real inference."""

import math
import numpy as np
from packages.tracking.features import Trajectories


class Scenario:
    duration = 150

    def __init__(self):
        self.trackers = {}

    def phase(self, t):
        if t < 15:
            return "Normal monitoring"
        if t < 42:
            return "Growing influx"
        if t < 95:
            return "Sustained congestion · connected zones"
        if t < 120:
            return "Flow recovering"
        return "Conditions normalized"

    def sample(self, camera_id, kind, t, timestamp):
        index = int(camera_id[-1]) if camera_id[-1].isdigit() else 1
        local = max(0, t - (index - 1) * 5)
        growth = max(0, min(1, (local - 15) / 28))
        recovery = max(0, min(1, (local - 95) / 25))
        count = (
            round((10 + 45 * growth) * (1 - 0.8 * recovery))
            if kind == "crowd"
            else round(4 + 10 * growth * (1 - recovery))
        )
        if index == 4:
            count = 12 + round(3 * math.sin(t / 12))
        detections = []
        for i in range(count):
            rng = np.random.default_rng(index * 1000 + i)
            px, py = rng.uniform(0.13, 0.84), rng.uniform(0.24, 0.85)
            movement = 0.002 if growth > 0.7 and recovery < 0.5 else 0.025
            x = px + math.sin(t * 0.7 + i) * movement
            y = py + math.cos(t * 0.5 + i) * movement
            # Road actors actually freeze during obstruction, yielding temporal stationary evidence.
            if kind == "road" and 45 < local < 105:
                x, y = px, py
            w = 0.024 if kind == "crowd" else 0.075
            h = 0.07 if kind == "crowd" else 0.04
            detections.append(
                {
                    "id": i + 1,
                    "class": "person" if kind == "crowd" else "car",
                    "confidence": 0.9,
                    "bbox": [
                        float(x - w / 2),
                        float(y - h),
                        float(x + w / 2),
                        float(y),
                    ],
                }
            )
        tracker = self.trackers.setdefault(camera_id, Trajectories())
        return tracker.update(detections, timestamp)
