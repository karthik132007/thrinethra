"""Lazy YOLO + ByteTrack integration; one instance per source, no cross-camera identities."""

from pathlib import Path
import time
from packages.tracking.features import Trajectories

CLASSES = [0, 1, 2, 3, 5, 7]


class Detector:
    def __init__(self, model_path, device="cpu", size=640, confidence=0.3):
        if not Path(model_path).is_file():
            raise FileNotFoundError(
                "Model missing. Run scripts/download_model.py before starting video inference."
            )
        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.device, self.size, self.confidence = device, size, confidence
        self.trajectories = Trajectories()

    def process(self, frame, timestamp):
        start = time.perf_counter()
        result = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=CLASSES,
            imgsz=self.size,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )[0]
        height, width = frame.shape[:2]
        detections = []
        if result.boxes is not None and result.boxes.id is not None:
            for box, cls, confidence, track in zip(
                result.boxes.xyxy.cpu().tolist(),
                result.boxes.cls.cpu().tolist(),
                result.boxes.conf.cpu().tolist(),
                result.boxes.id.cpu().tolist(),
            ):
                detections.append(
                    {
                        "id": int(track),
                        "class": result.names[int(cls)],
                        "confidence": round(confidence, 3),
                        "bbox": [
                            box[0] / width,
                            box[1] / height,
                            box[2] / width,
                            box[3] / height,
                        ],
                    }
                )
        tracks = self.trajectories.update(detections, timestamp)
        return tracks, (time.perf_counter() - start) * 1000
