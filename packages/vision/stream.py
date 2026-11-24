"""Bounded per-camera decoder/inference threads. A failed camera cannot stop its peers."""

import threading
import queue
import time
import cv2
from packages.vision.detector import Detector


class VideoWorker:
    def __init__(
        self, source, model_path, device="cpu", size=640, fps=2, confidence=0.3
    ):
        self.source = source
        self.args = (model_path, device, size, confidence)
        self.fps = fps
        self.frames = queue.Queue(maxsize=1)
        self.results = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()
        self.health = "starting"
        self.detail = ""
        self.dropped = 0
        self.threads = []

    def start(self):
        for target in (self.decode, self.infer):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self.threads.append(thread)
        return self

    def stop(self):
        self.stop_event.set()
        self.health = "stopped"

    @staticmethod
    def latest(buffer, item):
        if buffer.full():
            try:
                buffer.get_nowait()
            except queue.Empty:
                pass
        try:
            buffer.put_nowait(item)
        except queue.Full:
            pass

    def decode(self):
        while not self.stop_event.is_set():
            capture = cv2.VideoCapture()
            capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            source = (
                int(self.source.split(":")[1])
                if self.source.startswith("webcam:")
                else self.source
            )
            if not capture.open(source):
                self.health = "error"
                self.detail = "Unable to open source; retrying"
                capture.release()
                self.stop_event.wait(3)
                continue
            source_fps = capture.get(cv2.CAP_PROP_FPS) or 25
            file_source = not self.source.startswith(("rtsp:", "webcam:"))
            next_at = time.monotonic()
            frame_index = 0
            while not self.stop_event.is_set():
                ok, frame = capture.read()
                if not ok:
                    if file_source:
                        self.health = "ended"
                        self.detail = "File playback ended; restart stream to replay"
                        capture.release()
                        return
                    break
                frame_index += 1
                # Pace file playback and sample based on source timestamps; never decode a whole file as an instant.
                if file_source:
                    target = next_at + frame_index / source_fps
                    if self.stop_event.wait(max(0, target - time.monotonic())):
                        break
                if frame_index % max(1, round(source_fps / self.fps)) != 0:
                    continue
                if self.frames.full():
                    self.dropped += 1
                if max(frame.shape[:2]) > 1280:
                    scale = 1280 / max(frame.shape[:2])
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)
                self.latest(
                    self.frames,
                    (frame, time.time(), capture.get(cv2.CAP_PROP_POS_MSEC) / 1000),
                )
            capture.release()
            if not self.stop_event.is_set():
                self.health = "reconnecting"
                self.stop_event.wait(2)

    def infer(self):
        try:
            detector = Detector(*self.args)
        except Exception as exc:
            self.health = "error"
            self.detail = str(exc)
            self.stop_event.set()
            return
        while not self.stop_event.is_set():
            try:
                frame, timestamp, media_time = self.frames.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                tracks, latency = detector.process(frame, timestamp)
                self.latest(
                    self.results,
                    {
                        "tracks": tracks,
                        "timestamp": timestamp,
                        "latency_ms": latency,
                        "frame": frame,
                        "media_time": media_time,
                        "queue_latency_ms": (time.time() - timestamp) * 1000,
                    },
                )
                self.health = "online" if self.health != "ended" else "ended"
                if self.health != "ended":
                    self.detail = ""
            except Exception as exc:
                self.health = "error"
                self.detail = str(exc)
                self.stop_event.wait(1)


def render_frame(frame, tracks, polygon=None, blur=False):
    result = frame.copy()
    h, w = result.shape[:2]
    if blur:
        # Upper portion of every person box is blurred (privacy baseline, not a face detector).
        for track in tracks:
            if track["class"] != "person":
                continue
            a, b, c, d = track["bbox"]
            x1, x2 = max(0, int(a * w)), min(w, int(c * w))
            y1, y2 = max(0, int(b * h)), min(h, int((b + (d - b) * 0.35) * h))
            if x2 > x1 and y2 > y1:
                result[y1:y2, x1:x2] = cv2.GaussianBlur(
                    result[y1:y2, x1:x2], (31, 31), 15
                )
    if polygon:
        import numpy as np

        cv2.polylines(
            result,
            [np.array([[int(x * w), int(y * h)] for x, y in polygon])],
            True,
            (190, 170, 70),
            1,
        )
    for track in tracks:
        a, b, c, d = track["bbox"]
        start = (int(a * w), int(b * h))
        end = (int(c * w), int(d * h))
        cv2.rectangle(result, start, end, (160, 210, 100), 1)
        cv2.putText(
            result,
            f"{track['class']} #{track['id']}",
            start,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (160, 210, 100),
            1,
        )
    return cv2.imencode(".jpg", result, [cv2.IMWRITE_JPEG_QUALITY, 78])[1].tobytes()
