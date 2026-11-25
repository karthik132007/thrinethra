"""Bounded, independent per-camera decoding and inference with truthful timestamps."""

import threading
import queue
import time
import math
import cv2
from packages.vision.detector import Detector


class VideoWorker:
    def __init__(
        self,
        source,
        model_path,
        device="cpu",
        size=640,
        fps=2,
        confidence=0.3,
        crop=None,
    ):
        self.source = source
        self.args = (model_path, device, size, confidence)
        self.fps = max(0.1, fps)
        self.crop = crop
        self.frames = queue.Queue(maxsize=1)
        self.results = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()
        self.ready = threading.Event()
        self.decode_done = threading.Event()
        self.health = "starting"
        self.detail = "Loading detector"
        self.dropped = 0
        self.processed = 0
        self.source_frames = 0
        self.media_duration = 0.0
        self.media_time = 0.0
        self.last_result_at = None
        self.threads = []

    def start(self):
        for target in (self.infer, self.decode):
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
        # Initialize the model first so a short real clip is not lost during imports/warmup.
        while not self.ready.wait(0.1):
            if self.stop_event.is_set():
                return
        file_source = not self.source.startswith(("rtsp:", "webcam:"))
        try:
            while not self.stop_event.is_set():
                source = (
                    int(self.source.split(":")[1])
                    if self.source.startswith("webcam:")
                    else self.source
                )
                if self.source.startswith("rtsp:"):
                    capture = cv2.VideoCapture(
                        source,
                        cv2.CAP_FFMPEG,
                        [
                            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                            5000,
                            cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                            5000,
                        ],
                    )
                else:
                    capture = cv2.VideoCapture(source)
                if not capture.isOpened():
                    self.health = "error"
                    self.detail = "Unable to open source; retrying"
                    capture.release()
                    self.stop_event.wait(3)
                    continue
                source_fps = capture.get(cv2.CAP_PROP_FPS)
                if not math.isfinite(source_fps) or source_fps <= 0:
                    source_fps = 25.0
                self.source_frames = (
                    int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) if file_source else 0
                )
                self.media_duration = (
                    self.source_frames / source_fps if file_source else 0.0
                )
                start = time.monotonic()
                epoch = time.time()
                frame_index = 0
                next_sample = 0.0
                self.health = "online"
                self.detail = ""
                while not self.stop_event.is_set():
                    ok, frame = capture.read()
                    if not ok:
                        break
                    media_time = (
                        frame_index / source_fps
                        if file_source
                        else time.monotonic() - start
                    )
                    frame_index += 1
                    if file_source and self.stop_event.wait(
                        max(0, start + media_time - time.monotonic())
                    ):
                        break
                    if media_time + 1e-5 < next_sample:
                        continue
                    next_sample = media_time + 1 / self.fps
                    if self.crop:
                        h, w = frame.shape[:2]
                        a, b, c, d = self.crop
                        frame = frame[int(b * h) : int(d * h), int(a * w) : int(c * w)]
                    if max(frame.shape[:2]) > 1280:
                        scale = 1280 / max(frame.shape[:2])
                        frame = cv2.resize(frame, None, fx=scale, fy=scale)
                    if self.frames.full():
                        self.dropped += 1
                    # Use recording timeline for paced files; retain arrival separately for queue timing.
                    timestamp = epoch + media_time if file_source else time.time()
                    self.media_time = media_time
                    self.latest(
                        self.frames, (frame, timestamp, media_time, time.time())
                    )
                capture.release()
                if file_source:
                    self.detail = "Playback finished. Start to replay; tracking resets on restart."
                    return
                if not self.stop_event.is_set():
                    self.health = "reconnecting"
                    self.stop_event.wait(2)
        finally:
            self.decode_done.set()

    def infer(self):
        try:
            detector = Detector(*self.args)
        except Exception as exc:
            self.health = "error"
            self.detail = str(exc)
            self.stop_event.set()
            self.ready.set()
            return
        self.ready.set()
        while not self.stop_event.is_set():
            try:
                frame, timestamp, media_time, received = self.frames.get(timeout=0.25)
            except queue.Empty:
                if self.decode_done.is_set():
                    self.health = "ended"
                    return
                continue
            try:
                tracks, latency = detector.process(frame, timestamp)
                self.processed += 1
                self.last_result_at = time.time()
                self.latest(
                    self.results,
                    {
                        "tracks": tracks,
                        "model_info": getattr(detector,"metadata",{}),
                        "timestamp": timestamp,
                        "latency_ms": latency,
                        "frame": frame,
                        "media_time": media_time,
                        "queue_latency_ms": (time.time() - received) * 1000,
                    },
                )
                self.health = "online"
                if not self.decode_done.is_set():
                    self.detail = ""
            except Exception as exc:
                self.health = "error"
                self.detail = type(exc).__name__ + ": inference failed"
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
