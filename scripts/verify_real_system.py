"""Verify the running app using natural recordings, genuine model outputs and real local LLM."""

import json
import argparse
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--url",default="http://127.0.0.1:8000/api/v1");args=parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=180) as client:
        snapshot = client.get("/snapshot").json()
        assert not snapshot["demo"]["enabled"], (
            "The default workflow must not use simulation"
        )
        assert len(snapshot["cameras"]) == 4
        assert all(c["source"] == "video" for c in snapshot["cameras"])
        assert len(snapshot["latest"]) == 4 and all(
            l["provenance"] == "video_inference" for l in snapshot["latest"]
        )
        observations = {}
        for camera in snapshot["cameras"]:
            rows = client.get(
                "/observations", params={"camera_id": camera["id"], "limit": 100}
            ).json()["items"]
            rows = [r for r in rows if r["provenance"] == "video_inference"]
            assert len(rows) >= 5, (
                f"Insufficient real inference observations: {camera['id']}"
            )
            assert any(r["data"]["tracks"] for r in rows)
            assert any(any(t["speed"] > 0 for t in r["data"]["tracks"]) for r in rows)
            frame = client.get(f"/streams/{camera['id']}/frame")
            frame.raise_for_status()
            original = client.get(
                f"/streams/{camera['id']}/video", headers={"Range": "bytes=0-1023"}
            )
            assert original.status_code in (200, 206)
            observations[camera["id"]] = {
                "observations": len(rows),
                "count_min": min(r["data"]["count"] for r in rows),
                "count_max": max(r["data"]["count"] for r in rows),
                "mean_inference_ms": round(
                    sum(r["data"]["inference_ms"] for r in rows) / len(rows), 2
                ),
                "positive_motion_observations": sum(
                    any(t["speed"] > 0 for t in r["data"]["tracks"]) for r in rows
                ),
                "jpeg_bytes": len(frame.content),
                "original_video_range_status": original.status_code,
                "source_context": camera["source_metadata"]["context"],
            }
        incidents = [
            i
            for i in snapshot["incidents"]
            if i["event"]["provenance"] == "video_inference"
        ]
        assert incidents, "No measured sustained condition generated an incident"
        incident = incidents[0]
        id = incident["id"]
        detail = client.get("/incidents/" + id).json()
        assert detail["evidence"]
        started = time.perf_counter()
        response = client.post(
            "/investigations/" + id,
            json={
                "question": "Why was this incident raised? Explain the measured evidence and what is still uncertain."
            },
        )
        response.raise_for_status()
        report = response.json()["data"]
        latency = time.perf_counter() - started
        assert report.get("model_reasoning", {}).get("citations_validated"), report[
            "limitations"
        ]
        assert "local Ollama" in report["mode"]
        refs = {e["id"] for e in detail["evidence"]}
        assert set(report["model_reasoning"]["data"]["evidence_references"]) <= refs
        for observation in report["observations"]:
            assert set(observation["evidence_references"]) <= refs
        for status in ("verified", "resolved"):
            response = client.patch(
                "/incidents/" + id + "/review",
                json={
                    "status": status,
                    "note": "Real recording integration verification; no operational response.",
                },
            )
            response.raise_for_status()
        result = {
            "provenance": "Actual running natural-video pipeline; no synthetic observations",
            "sources": observations,
            "incidents": len(incidents),
            "incident_under_test": {
                "id": id,
                "type": incident["event"]["type"],
                "camera": incident["event"]["camera_id"],
            },
            "investigation_seconds": round(latency, 3),
            "investigation_mode": report["mode"],
            "model_reasoning": report["model_reasoning"],
            "retained_evidence_references": report["evidence_references"],
            "operator_review_verified_and_resolved": True,
            "limitations": [
                "Night-crowd detector misses are measured separately; this is not safety validation.",
                "Connected cropped views share one source recording.",
                "No autonomous actions are dispatched.",
            ],
        }
        (ROOT / "evaluations/real-system-results.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
