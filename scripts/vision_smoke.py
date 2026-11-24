"""Real YOLO/ByteTrack smoke on a locally supplied video, plus measured CPU performance.

Default fixture is a video encoded from the upstream bus.jpg test photograph: real image
inference, but NOT natural motion footage and NOT annotated accuracy evaluation.
"""

import os

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/trinethra-yolo")
import sys
import time
import json
from pathlib import Path
import cv2
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.vision.detector import Detector


def main():
    image = cv2.imread(str(ROOT / "runtime/media/bus.jpg"))
    if image is None:
        raise SystemExit(
            "Supply runtime/media/bus.jpg from the upstream Ultralytics asset or pass a video path."
        )
    path = ROOT / "runtime/media/inference-smoke.avi"
    height, width = image.shape[:2]
    scale = 640 / max(height, width)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    h, w = image.shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 8, (w, h))
    for _ in range(64):
        writer.write(image)
    writer.release()
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else path
    detector = Detector(ROOT / "runtime/models/yolo11n.pt", size=640)
    capture = cv2.VideoCapture(str(source))
    results = []
    ids = []
    detections = []
    process = psutil.Process()
    process.cpu_percent()
    for index in range(12):
        ok, frame = capture.read()
        if not ok:
            break
        tracks, ms = detector.process(frame, time.time() + index / 8)
        results.append(ms)
        ids.append({t["id"] for t in tracks})
        detections.append({t["class"] for t in tracks})
    capture.release()
    assert results and any(ids), "No real detections or track IDs produced"
    steady = results[1:] or results
    data = {
        "fixture": "Locally encoded repeated real bus photograph; no natural scene dynamics",
        "source": str(source.relative_to(ROOT))
        if source.is_relative_to(ROOT)
        else str(source),
        "frames": len(results),
        "classes_detected": sorted(set.union(*detections)),
        "stable_track_ids": sorted(set.intersection(*ids)),
        "first_frame_ms": round(results[0], 2),
        "mean_inference_ms_excluding_first": round(float(np.mean(steady)), 2),
        "inference_fps_excluding_first": round(1000 / float(np.mean(steady)), 2),
        "p95_inference_ms_excluding_first": round(float(np.percentile(steady, 95)), 2),
        "rss_mb": round(process.memory_info().rss / 1024**2, 1),
        "process_cpu_percent": process.cpu_percent(),
        "device": "cpu",
        "size": 640,
        "accuracy": "Not evaluated; no ground truth annotations",
        "natural_video_dynamics": "Not evaluated",
    }
    (ROOT / "evaluations/vision-results.json").write_text(
        json.dumps(data, indent=2) + "\n"
    )
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
