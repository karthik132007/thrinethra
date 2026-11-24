"""Verify upload -> worker -> detector/tracker -> observations -> annotated frame through HTTP."""

import json
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v1", timeout=30) as client:
        cameras = client.get("/cameras").json()
        camera = next(c for c in cameras if c["id"] == "cam-04")
        assert camera["source"] == "synthetic", (
            "This smoke uses the disposable synthetic cam-04; do not replace a personal video source."
        )
        body = {key: camera[key] for key in ("name", "lat", "lon", "kind", "enabled")}
        with (ROOT / "runtime/media/inference-smoke.avi").open("rb") as file:
            response = client.post(
                "/streams/upload",
                files={"file": ("inference-smoke.avi", file, "video/x-msvideo")},
            )
            response.raise_for_status()
            source = response.json()["source"]
        start = time.time()
        response = client.put("/cameras/cam-04", json=body | {"source": source})
        response.raise_for_status()
        try:
            observation = None
            for _ in range(90):
                time.sleep(0.5)
                response = client.get(
                    "/observations",
                    params={"camera_id": "cam-04", "since": start, "limit": 10},
                )
                response.raise_for_status()
                rows = response.json()["items"]
                observation = next(
                    (
                        r
                        for r in rows
                        if r["provenance"] == "video_inference" and r["data"]["tracks"]
                    ),
                    None,
                )
                if observation:
                    break
            assert observation, (
                "No real inference observation produced within 45 seconds"
            )
            frame = client.get("/streams/cam-04/frame")
            frame.raise_for_status()
            assert frame.headers["content-type"] == "image/jpeg"
            tracks = observation["data"]["tracks"]
            health = client.get("/health").json()
            data = {
                "provenance": "video_inference",
                "fixture": "Uploaded video encoded from a repeated real photograph",
                "upload_validated": True,
                "tracks": len(tracks),
                "track_classes": sorted({r["class"] for r in tracks}),
                "annotated_frame_bytes": len(frame.content),
                "first_observation_wall_seconds": round(time.time() - start, 3),
                "observation_inference_ms": observation["data"]["inference_ms"],
                "queue_to_result_ms": observation["data"]["queue_latency_ms"],
                "backend_rss_mb": health["memory_mb"],
                "limitations": "No natural-motion accuracy or safety validation. Warm-up included in first observation wall time.",
            }
            (ROOT / "evaluations/pipeline-results.json").write_text(
                json.dumps(data, indent=2) + "\n"
            )
            print(json.dumps(data, indent=2))
        finally:
            client.put(
                "/cameras/cam-04", json=body | {"source": "synthetic"}
            ).raise_for_status()


if __name__ == "__main__":
    main()
