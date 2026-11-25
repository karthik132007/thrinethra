"""Reproducible natural-video inference and MOT17 annotated pedestrian evaluation.

Raw official preview videos are half-resolution versions of the annotated sequences.
Boxes are normalized by the annotation dimensions, preserving alignment. No retraining,
synthetic observations or cached detector outputs are used by this script.
"""

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "apps/backend")]
os.environ.setdefault("TORCH_THREADS", "2")
from packages.vision.detector import Detector
from packages.vision.stream import render_frame
from packages.forecasting.baseline import forecast


def iou_matrix(pred, truth):
    if not pred or not truth:
        return np.zeros((len(pred), len(truth)))
    a = np.asarray(pred)
    b = np.asarray(truth)
    lo = np.maximum(a[:, None, :2], b[None, :, :2])
    hi = np.minimum(a[:, None, 2:], b[None, :, 2:])
    overlap = np.prod(np.maximum(0, hi - lo), axis=2)
    return overlap / np.maximum(
        1e-9,
        np.prod(a[:, 2:] - a[:, :2], axis=1)[:, None]
        + np.prod(b[:, 2:] - b[:, :2], axis=1)[None, :]
        - overlap,
    )


def match_boxes(pred, truth):
    import lap

    iou = iou_matrix(pred, truth)
    if not iou.size:
        return [], len(pred), len(truth)
    _, assigned, _ = lap.lapjv(1 - iou, extend_cost=True, cost_limit=0.500001)
    matches = [
        (i, int(j)) for i, j in enumerate(assigned) if j >= 0 and iou[i, j] >= 0.5
    ]
    return matches, len(pred) - len(matches), len(truth) - len(matches)


def evaluate_video(asset, model, sample_fps=2, size=640):
    path = ROOT / asset["path"]
    capture = cv2.VideoCapture(str(path))
    fps = capture.get(cv2.CAP_PROP_FPS)
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    assert fps > 0 and total > 1, f"Undecodable {path}"
    detector = Detector(ROOT / "runtime/models" / model, size=size)
    annotation = None
    if asset["id"] in ("mot04", "mot09"):
        seq = "MOT17-04-FRCNN" if asset["id"] == "mot04" else "MOT17-09-FRCNN"
        annotation = np.loadtxt(
            ROOT / "runtime/datasets/train" / seq / "gt/gt.txt", delimiter=","
        )
    records = []
    times = []
    classes = Counter()
    tp = fp = fn = 0
    count_errors = []
    last_assign = {}
    switches = 0
    matches_total = 0
    track_positions = {}
    max_motion = 0
    previous = None
    pixel_changes = []
    stride = max(1, round(fps / sample_fps))
    start = time.perf_counter()
    for index in range(total):
        ok, frame = capture.read()
        if not ok:
            break
        if index % stride:
            continue
        t = index / fps
        tracks, latency = detector.process(frame, 1_000_000 + t)
        times.append(latency)
        counts = Counter(row["class"] for row in tracks)
        classes.update(counts)
        for track in tracks:
            if track["id"] in track_positions:
                max_motion = max(
                    max_motion, math.dist(track["center"], track_positions[track["id"]])
                )
            track_positions[track["id"]] = track["center"]
        thumbnail = cv2.resize(frame, (160, 90)).astype(float)
        if previous is not None:
            pixel_changes.append(float(np.mean(abs(thumbnail - previous))))
        previous = thumbnail
        record = {
            "frame": index + 1,
            "media_time": round(t, 3),
            "count": counts["person"],
            "vehicles": sum(v for k, v in counts.items() if k != "person"),
            "classes": dict(counts),
            "latency_ms": round(latency, 3),
            "track_ids": [track["id"] for track in tracks],
        }
        if annotation is not None:
            rows = annotation[
                (annotation[:, 0] == index + 1)
                & (annotation[:, 6] == 1)
                & (annotation[:, 7] == 1)
            ]
            truth = [
                [r[2] / 1920, r[3] / 1080, (r[2] + r[4]) / 1920, (r[3] + r[5]) / 1080]
                for r in rows
            ]
            people = [track for track in tracks if track["class"] == "person"]
            matched, extra, missing = match_boxes([r["bbox"] for r in people], truth)
            tp += len(matched)
            fp += extra
            fn += missing
            count_errors.append(len(people) - len(truth))
            for p, g in matched:
                gt_id = int(rows[g, 1])
                track_id = people[p]["id"]
                if gt_id in last_assign and last_assign[gt_id] != track_id:
                    switches += 1
                last_assign[gt_id] = track_id
                matches_total += 1
            record["ground_truth_count"] = len(truth)
        records.append(record)
        if len(records) in (1, 10, 30):
            output = (
                ROOT
                / "runtime/evaluation-frames"
                / f"{asset['id']}-{model}-{index + 1}.jpg"
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(render_frame(frame, tracks, blur=True))
    capture.release()
    errors = []
    baseline = []
    for index in range(10, len(records) - 2):
        history = [
            {"timestamp": r["media_time"], "count": r["count"]}
            for r in records[max(0, index - 20) : index]
        ]
        horizon = records[index + 2]["media_time"] - history[-1]["timestamp"]
        predicted = forecast(history, 100, horizon)
        if predicted["ready"]:
            target = records[index + 2]["count"]
            errors.append(predicted["points"][-1]["value"] - target)
            baseline.append(history[-1]["count"] - target)
    result = {
        "asset": asset["id"],
        "sha256": asset["sha256"],
        "source_url": asset["url"],
        "provenance": "real natural-motion video inference",
        "model": model,
        "size": size,
        "sample_fps": sample_fps,
        "video_fps": fps,
        "video_frames": total,
        "sampled_frames": len(records),
        "duration_seconds": round(total / fps, 3),
        "classes_detected": dict(classes),
        "distinct_temporary_track_ids": len(track_positions),
        "max_matched_track_displacement_normalized": round(max_motion, 5),
        "mean_frame_pixel_change_160x90": round(float(np.mean(pixel_changes)), 3),
        "mean_inference_ms": round(float(np.mean(times)), 3),
        "p95_inference_ms": round(float(np.percentile(times, 95)), 3),
        "wall_seconds": round(time.perf_counter() - start, 3),
        "process_rss_mb": round(psutil.Process().memory_info().rss / 1024**2, 1),
        "observations": records,
    }
    if annotation is not None:
        result["annotated_pedestrians"] = {
            "iou_threshold": 0.5,
            "ground_truth_filter": "MOT valid=1 and class=1; all visibility levels. Raw published half-resolution sequence; GT normalized by original 1920x1080 dimensions.",
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(tp / max(1, tp + fp), 4),
            "recall": round(tp / max(1, tp + fn), 4),
            "count_mae": round(float(np.mean(np.abs(count_errors))), 3),
            "count_rmse": round(float(np.sqrt(np.mean(np.square(count_errors)))), 3),
            "sampled_identity_switches": switches,
            "matched_boxes": matches_total,
            "limitations": "Sparse-frame matches and ID switches are diagnostics, not official MOTChallenge HOTA/MOTA/IDF1. Ignored/distractor regions are not suppressed; preview compression affects accuracy.",
        }
    if errors:
        result["forecast_on_detected_counts"] = {
            "cases": len(errors),
            "selected_model_mae": round(float(np.mean(np.abs(errors))), 3),
            "last_value_mae": round(float(np.mean(np.abs(baseline))), 3),
            "target": "Future detector-derived person counts, not future ground-truth safety conditions",
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=640)
    parser.add_argument("--output", default="real-video-results.json")
    parser.add_argument("--models", nargs="+", default=["yolo11n.pt", "yolo11s.pt"])
    parser.add_argument(
        "--assets", nargs="+", default=["mot04", "mot09", "people", "traffic"]
    )
    args = parser.parse_args()
    assets = json.loads((ROOT / "configs/assets.json").read_text())["assets"]
    results = []
    for model in args.models:
        for asset in assets:
            if asset["id"] not in args.assets:
                continue
            print(f"Inferring {asset['id']} with {model}", flush=True)
            row = evaluate_video(asset, model, size=args.size)
            results.append(row)
            print(
                json.dumps({k: v for k, v in row.items() if k != "observations"}),
                flush=True,
            )
            (ROOT / "evaluations" / args.output).write_text(
                json.dumps(
                    {
                        "data": "Natural-motion source recordings; actual fresh model inference",
                        "results": results,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
