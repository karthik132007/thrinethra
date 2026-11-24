"""Camera-local trajectory features. Coordinates and speeds are normalized image-plane units."""

from collections import deque
import math


class Trajectories:
    def __init__(self, ttl=8):
        self.history = {}
        self.ttl = ttl

    def update(self, detections, timestamp):
        for key in list(self.history):
            if timestamp - self.history[key][-1][0] > self.ttl:
                del self.history[key]
        output = []
        for detection in detections:
            item = dict(detection)
            x1, y1, x2, y2 = item["bbox"]
            center = ((x1 + x2) / 2, y2)
            history = self.history.setdefault(item["id"], deque(maxlen=60))
            previous_speed = 0
            if len(history) > 1:
                a, b = history[-2], history[-1]
                previous_speed = math.hypot(b[1] - a[1], b[2] - a[2]) / max(
                    b[0] - a[0], 0.001
                )
            dt = timestamp - history[-1][0] if history else 0
            vx = (center[0] - history[-1][1]) / dt if dt > 0 else 0
            vy = (center[1] - history[-1][2]) / dt if dt > 0 else 0
            speed = math.hypot(vx, vy)
            history.append((timestamp, *center))
            item.update(
                center=list(center),
                velocity=[vx, vy],
                speed=speed,
                sudden_stop=previous_speed > 0.035 and speed < previous_speed * 0.25,
                dwell=timestamp - history[0][0],
                trajectory=[list(p) for p in history],
                direction=math.degrees(math.atan2(vy, vx)) if speed else 0,
            )
            output.append(item)
        return output
