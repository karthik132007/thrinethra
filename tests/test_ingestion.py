import queue
import time
import cv2
import numpy as np
from packages.vision.stream import VideoWorker


def test_bounded_latest_queue_drops_old_entries():
    buffer = queue.Queue(maxsize=1)
    for i in range(100):
        VideoWorker.latest(buffer, i)
    assert buffer.qsize() == 1
    assert buffer.get_nowait() == 99


def test_independent_decoder_worker_and_failed_camera(tmp_path, monkeypatch):
    class StubDetector:
        def __init__(self, *args):
            pass

        def process(self, frame, timestamp):
            return [], 1.0

    monkeypatch.setattr("packages.vision.stream.Detector", StubDetector)
    file = tmp_path / "input.avi"
    writer = cv2.VideoWriter(str(file), cv2.VideoWriter_fourcc(*"MJPG"), 10, (160, 100))
    for _ in range(10):
        writer.write(np.zeros((100, 160, 3), dtype=np.uint8))
    writer.release()
    valid = VideoWorker(str(file), "unused", fps=5).start()
    failed = VideoWorker(str(tmp_path / "missing.avi"), "unused").start()
    try:
        result = valid.results.get(timeout=5)
        assert result["frame"].shape == (100, 160, 3)
        assert result["tracks"] == []
        assert result["latency_ms"] == 1
        assert valid is not failed
        assert valid.frames.maxsize == 1
        assert valid.results.maxsize == 2
    finally:
        valid.stop()
        failed.stop()
        for worker in (valid, failed):
            for thread in worker.threads:
                thread.join(timeout=2)
