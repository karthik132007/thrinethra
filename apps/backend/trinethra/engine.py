import asyncio
import json
import logging
import queue
import time
from collections import deque
from pathlib import Path
import cv2
import numpy as np
import yaml
from sqlalchemy import select, delete
from .config import ROOT, RUNTIME, settings
from .assets import camera_metadata, recording_config
from .db import (
    Session,
    Camera,
    Zone,
    Connection,
    Observation,
    TrackMeasurement,
    Event,
    Incident,
    Correlation,
    RiskAssessment,
    Forecast,
    Evidence,
    Investigation,
    Feedback,
    Configuration,
    AuditLog,
    serialize,
    now,
    uid,
)
from packages.intelligence.analytics import Analytics, DEFAULTS, risk_score
from packages.forecasting.baseline import forecast
from packages.correlation.graph import correlate
from packages.vision.stream import VideoWorker, render_frame
from demo.scenario import Scenario

log = logging.getLogger("trinethra.engine")
TITLES = {
    "potential_crowd_safety_risk": "Potential crowd safety risk",
    "bottleneck": "Sustained crowd bottleneck",
    "sudden_crowd_movement": "Sudden crowd movement",
    "traffic_obstruction": "Possible traffic obstruction",
    "abnormal_traffic_congestion": "Abnormal traffic congestion",
    "restricted_zone_stop": "Vehicle stopped in restricted zone",
    "suspected_road_incident": "Suspected road incident · verification required",
}


class Engine:
    def __init__(self):
        self.analytics = Analytics()
        self.scenario = Scenario()
        self.latest = {}
        self.histories = {}
        self.frames = {}
        self.workers = {}
        self.run_started = {}
        self.running = True
        self.paused = False
        self.demo_time = 0.0
        self.speed = 2.0
        self.last_tick = time.monotonic()
        self.started = time.monotonic()
        self.tick_ms = 0.0
        self.error = ""
        self.last_retention = 0

    def seed(self):
        config_path = ROOT / (
            "configs/cameras.yaml"
            if settings.synthetic_mode
            else "configs/cameras.real.yaml"
        )
        data = yaml.safe_load(config_path.read_text())
        with Session.begin() as db:
            # Disable old synthetic fixtures in the real workflow without deleting history.
            if not settings.synthetic_mode:
                for previous in db.scalars(
                    select(Camera).where(Camera.source == "synthetic")
                ):
                    previous.enabled = False
            for original in data["cameras"]:
                camera = dict(original)
                zone_id = camera.pop("zone_id")
                capacity = camera.pop(
                    "capacity", 16 if camera["kind"] == "road" else 40
                )
                camera.pop("crop", None)
                camera.pop("recording_group", None)
                camera.setdefault("source", "synthetic")
                if camera["source"].startswith("media:"):
                    camera["source"] = str(
                        (RUNTIME / "media" / camera["source"][6:]).resolve()
                    )
                if db.get(Camera, camera["id"]):
                    continue
                db.add(Camera(**camera))
                db.flush()
                db.add(
                    Zone(
                        id=zone_id,
                        camera_id=camera["id"],
                        name=camera["name"] + " zone",
                        capacity=capacity,
                        restricted=False,
                    )
                )
            db.flush()
            for a, b in data.get("connections", []):
                if not db.scalar(
                    select(Connection).where(
                        Connection.camera_a == a, Connection.camera_b == b
                    )
                ):
                    db.add(Connection(camera_a=a, camera_b=b))
            if not db.get(Configuration, "intelligence"):
                db.add(Configuration(id="intelligence", data=DEFAULTS))

    def configuration(self):
        with Session() as db:
            row = db.get(Configuration, "intelligence")
            return DEFAULTS | (row.data if row else {})

    def start_worker(self, camera):
        if camera["id"] in self.workers:
            self.workers.pop(camera["id"]).stop()
        self.run_started[camera["id"]] = now()
        self.workers[camera["id"]] = VideoWorker(
            camera["source"],
            str(ROOT / settings.model_path),
            settings.device,
            settings.inference_size,
            settings.sample_fps,
            self.configuration()["confidence_threshold"],
            crop=camera_metadata(camera).get("crop"),
        ).start()

    def restart_recording(self, camera):
        with Session.begin() as db:
            for event in db.scalars(
                select(Event).where(
                    Event.camera_id == camera["id"],
                    Event.status.in_(
                        ["active", "escalated", "under_review", "verified"]
                    ),
                )
            ):
                event.status = "resolved"
                event.updated_at = now()
                incident = db.scalar(
                    select(Incident).where(Incident.event_id == event.id)
                )
                incident.timeline = incident.timeline + [
                    {
                        "timestamp": now(),
                        "status": "resolved",
                        "note": "Recording restarted; beginning a new tracking/observation run",
                    }
                ]
        self.stop_worker(camera["id"])
        self.clear_camera(camera["id"])
        self.start_worker(camera)

    def stop_worker(self, camera_id):
        if camera_id in self.workers:
            self.workers.pop(camera_id).stop()

    def clear_camera(self, camera_id):
        self.latest.pop(camera_id, None)
        self.histories.pop(camera_id, None)
        self.frames.pop(camera_id, None)
        self.scenario.trackers.pop(camera_id, None)
        with Session() as db:
            zone_ids = [
                z.id
                for z in db.scalars(select(Zone).where(Zone.camera_id == camera_id))
            ]
        for zone_id in zone_ids:
            self.histories.pop(zone_id, None)
            self.latest.pop(zone_id, None)
            self.analytics.history.pop(zone_id, None)
            for key in list(self.analytics.since):
                if key[0] == zone_id:
                    self.analytics.since.pop(key, None)
        for key in list(self.analytics.abrupt):
            if key[0] in zone_ids:
                self.analytics.abrupt.pop(key, None)
        for key in list(self.analytics.stationary):
            if key[0] == camera_id:
                self.analytics.stationary.pop(key, None)

    async def loop(self):
        self.seed()
        with Session() as db:
            for camera in db.scalars(select(Camera).where(Camera.enabled == True)):
                if camera.source != "synthetic":
                    self.start_worker(serialize(camera))
        while self.running:
            start = time.monotonic()
            elapsed = start - self.last_tick
            self.last_tick = start
            if not self.paused:
                self.demo_time = min(
                    Scenario.duration, self.demo_time + elapsed * self.speed
                )
            try:
                config = self.configuration()
                with Session() as db:
                    cameras = [serialize(c) for c in db.scalars(select(Camera))]
                    zones = [serialize(z) for z in db.scalars(select(Zone))]
                for camera in cameras:
                    try:
                        self.process_camera(camera, zones, config)
                    except Exception as exc:
                        log.exception(
                            "camera_processing_failed",
                            extra={"camera_id": camera["id"]},
                        )
                        with Session.begin() as db:
                            row = db.get(Camera, camera["id"])
                            row.health = "error"
                            row.detail = type(exc).__name__ + ": processing failed"
                if now() - self.last_retention > 300:
                    self.retain()
                    self.last_retention = now()
                self.error = ""
            except Exception as exc:
                log.exception("engine_tick_failed")
                self.error = type(exc).__name__
            self.tick_ms = (time.monotonic() - start) * 1000
            await asyncio.sleep(max(0.1, 1 - (time.monotonic() - start)))

    def process_camera(self, camera, zones, config):
        if not camera["enabled"]:
            return
        camera_zones = [z for z in zones if z["camera_id"] == camera["id"]]
        if camera["source"] == "synthetic":
            if not settings.synthetic_mode or not settings.demo_mode or self.paused:
                return
            tracks = (
                self.scenario.sample(
                    camera["id"], camera["kind"], self.demo_time, now()
                )
                if self.demo_time < Scenario.duration
                else []
            )
            frame = self.synthetic_frame(camera, tracks)
            for zone in camera_zones:
                self.process(
                    camera,
                    zone,
                    tracks,
                    now(),
                    "synthetic",
                    0,
                    frame,
                    0,
                    0,
                    config,
                )
        elif camera["id"] in self.workers:
            worker = self.workers[camera["id"]]
            with Session.begin() as db:
                row = db.get(Camera, camera["id"])
                row.health = worker.health
                row.detail = worker.detail[:500]
            try:
                result = worker.results.get_nowait()
            except queue.Empty:
                return
            for zone in camera_zones:
                self.process(
                    camera,
                    zone,
                    result["tracks"],
                    result["timestamp"],
                    "video_inference",
                    result["latency_ms"],
                    result["frame"],
                    result["media_time"],
                    result["queue_latency_ms"],
                    config,
                    model_info=result.get("model_info"),
                )

    def synthetic_frame(self, camera, tracks):
        frame = np.full((450, 800, 3), (24, 29, 33), dtype=np.uint8)
        if camera["kind"] == "road":
            cv2.rectangle(frame, (0, 130), (800, 350), (42, 47, 50), -1)
            for x in range(0, 800, 90):
                cv2.line(frame, (x, 240), (x + 45, 240), (90, 97, 100), 2)
            cv2.rectangle(frame, (320, 0), (480, 450), (42, 47, 50), -1)
        else:
            for x in range(0, 800, 55):
                cv2.line(frame, (x, 0), (x, 450), (34, 40, 43), 1)
            for y in range(0, 450, 55):
                cv2.line(frame, (0, y), (800, y), (34, 40, 43), 1)
            cv2.rectangle(frame, (20, 20), (175, 75), (39, 46, 48), -1)
            cv2.rectangle(frame, (620, 340), (780, 430), (39, 46, 48), -1)
        cv2.putText(
            frame,
            "SYNTHETIC SCENARIO - NO VIDEO INFERENCE",
            (18, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 195, 205),
            1,
        )
        for track in tracks:
            x, y = track["center"]
            pos = (int(x * 800), int(y * 450))
            if track["class"] == "person":
                cv2.circle(frame, (pos[0], pos[1] - 13), 4, (170, 182, 190), -1)
                cv2.line(frame, (pos[0], pos[1] - 9), pos, (170, 182, 190), 3)
            else:
                cv2.rectangle(
                    frame,
                    (pos[0] - 20, pos[1] - 12),
                    (pos[0] + 20, pos[1]),
                    (145, 155, 166),
                    -1,
                )
        return frame

    def process(
        self,
        camera,
        zone,
        tracks,
        timestamp,
        provenance,
        latency,
        frame,
        media_time,
        queue_latency,
        config,
        model_info=None,
    ):
        metric, signals = self.analytics.analyze(
            camera["id"], zone, tracks, timestamp, config, camera["kind"]
        )
        history = self.histories.setdefault(zone["id"], deque(maxlen=120))
        history.append(
            {"timestamp": timestamp, "count": metric["count"], "provenance": provenance}
        )
        prediction = forecast(
            list(history), zone["capacity"], config["forecast_horizon"]
        )
        prediction["provenance"] = provenance
        with Session.begin() as db:
            camera_row = db.get(Camera, camera["id"])
            camera_row.health = "synthetic" if provenance == "synthetic" else "online"
            observation = Observation(
                camera_id=camera["id"],
                zone_id=zone["id"],
                timestamp=timestamp,
                provenance=provenance,
                data=metric
                | {
                    "inference_ms": round(latency, 2),
                    "media_time": media_time,
                    "recording_run_started_at": self.run_started.get(camera["id"]),
                    "model": model_info,
                    "queue_latency_ms": round(queue_latency, 2),
                },
            )
            db.add(observation)
            db.flush()
            db.add(
                TrackMeasurement(
                    observation_id=observation.id,
                    data={
                        "count": len(tracks),
                        "mean_speed": metric["mean_speed"],
                        "direction": metric["direction"],
                    },
                )
            )
            connections = {
                frozenset((c.camera_a, c.camera_b))
                for c in db.scalars(select(Connection))
            }
            active = list(
                db.scalars(
                    select(Event).where(
                        Event.status.in_(
                            ["active", "escalated", "under_review", "verified"]
                        )
                    )
                )
            )
            nearby = sum(
                1
                for e in active
                if e.provenance == provenance
                and frozenset((e.camera_id, camera["id"])) in connections
            )
            risk = risk_score(metric, prediction, nearby, config)
            db.add(
                RiskAssessment(
                    observation_id=observation.id,
                    score=risk["score"],
                    level=risk["level"],
                    components=risk["components"],
                )
            )
            if len(history) % 5 == 0:
                db.add(
                    Forecast(
                        camera_id=camera["id"],
                        timestamp=timestamp,
                        data=prediction | {"zone_id": zone["id"]},
                    )
                )
            active_types = set()
            for signal in signals:
                active_types.add(signal["type"])
                event = next(
                    (
                        e
                        for e in active
                        if e.zone_id == zone["id"]
                        and e.type == signal["type"]
                        and e.provenance == provenance
                    ),
                    None,
                )
                if event is None:
                    recent = db.scalar(
                        select(Event)
                        .where(
                            Event.zone_id == zone["id"],
                            Event.type == signal["type"],
                            Event.updated_at > timestamp - config["cooldown_seconds"],
                        )
                        .order_by(Event.updated_at.desc())
                    )
                    if recent:
                        continue
                    event = Event(
                        camera_id=camera["id"],
                        zone_id=zone["id"],
                        type=signal["type"],
                        started_at=timestamp,
                        updated_at=timestamp,
                        severity=risk["level"],
                        confidence=signal["confidence"],
                        status="active",
                        verification="unverified",
                        provenance=provenance,
                        factors=signal["factors"],
                        tracks=signal["tracks"],
                        evidence_refs=[],
                    )
                    db.add(event)
                    db.flush()
                    incident = Incident(
                        event_id=event.id,
                        title=TITLES.get(event.type, event.type),
                        timeline=[
                            {
                                "timestamp": timestamp,
                                "status": "active",
                                "note": "Temporal threshold met",
                            }
                        ],
                    )
                    db.add(incident)
                    db.flush()
                    for other in active:
                        other_camera = db.get(Camera, other.camera_id)
                        other_metric = self.latest.get(other.zone_id, {}).get(
                            "metrics", {}
                        )
                        current_meta = camera_metadata(camera)
                        other_meta = camera_metadata(other_camera)
                        common = current_meta.get(
                            "recording_group"
                        ) and current_meta.get("recording_group") == other_meta.get(
                            "recording_group"
                        )
                        flow_reference = current_meta.get("recording_group") if common and current_meta.get("crop") and other_meta.get("crop") else None
                        relation = correlate(
                            serialize(event)
                            | {
                                "flow_reference": flow_reference,
                                "direction": metric["direction"],
                                "mean_speed": metric["mean_speed"],
                            },
                            serialize(other)
                            | {
                                "flow_reference": flow_reference,
                                "direction": other_metric.get("direction", 0),
                                "mean_speed": other_metric.get("mean_speed", 0),
                            },
                            connections,
                        )
                        if relation and common:
                            relation["explanation"] += (
                                " Adjacent cropped views of one recording; not independent physical cameras or verified GPS proximity."
                                if current_meta.get("crop") else
                                " Publisher-synchronized different physical cameras of the same area; no identities matched and no GPS proximity asserted."
                            )
                        other_incident = db.scalar(
                            select(Incident).where(Incident.event_id == other.id)
                        )
                        if relation and other_incident:
                            db.add(
                                Correlation(
                                    incident_a=incident.id,
                                    incident_b=other_incident.id,
                                    timestamp=timestamp,
                                    **relation,
                                )
                            )
                    db.add(
                        AuditLog(
                            action="incident_created",
                            subject=incident.id,
                            data={"provenance": provenance},
                        )
                    )
                else:
                    old = event.severity
                    event.updated_at = timestamp
                    event.factors = signal["factors"]
                    event.confidence = signal["confidence"]
                    event.tracks = signal["tracks"]
                    event.severity = risk["level"]
                    if risk["level"] == "critical" and event.status == "active":
                        event.status = "escalated"
                        incident = db.scalar(
                            select(Incident).where(Incident.event_id == event.id)
                        )
                        incident.timeline = incident.timeline + [
                            {
                                "timestamp": timestamp,
                                "status": "escalated",
                                "note": "Experimental risk reached critical threshold",
                            }
                        ]
                # Keep bounded evidence snapshots, one initial and subsequent at 15 second intervals.
                last = db.scalar(
                    select(Evidence)
                    .where(Evidence.event_id == event.id)
                    .order_by(Evidence.timestamp.desc())
                )
                if not last or timestamp - last.timestamp >= 15:
                    evidence_id = uid()
                    relative = f"{evidence_id}.jpg"
                    (RUNTIME / "evidence" / relative).write_bytes(
                        render_frame(
                            frame, tracks, zone["polygon"], settings.blur_evidence
                        )
                    )
                    evidence = Evidence(
                        id=evidence_id,
                        event_id=event.id,
                        observation_id=observation.id,
                        timestamp=timestamp,
                        path=relative,
                        provenance=provenance,
                        data={
                            "factors": signal["factors"],
                            "count": metric["count"],
                            "media_time": media_time,
                            "model": model_info,
                            "risk": risk,
                            "tracks": [
                                {
                                    "id": t["id"],
                                    "velocity": t["velocity"],
                                    "dwell": t["dwell"],
                                }
                                for t in tracks
                            ],
                            "event_latency_ms": round((now() - timestamp) * 1000, 2),
                            "privacy": "Upper-person-box blur"
                            if settings.blur_evidence
                            else "disabled",
                        },
                    )
                    db.add(evidence)
                    event.evidence_refs = event.evidence_refs + [evidence_id]
            for event in active:
                if (
                    event.zone_id == zone["id"]
                    and event.provenance == provenance
                    and event.type not in active_types
                    and timestamp - event.updated_at > 8
                ):
                    event.status = "resolved"
                    incident = db.scalar(
                        select(Incident).where(Incident.event_id == event.id)
                    )
                    incident.timeline = incident.timeline + [
                        {
                            "timestamp": timestamp,
                            "status": "resolved",
                            "note": "Observed conditions normalized for 8 seconds",
                        }
                    ]
        self.frames[camera["id"]] = render_frame(frame, tracks, zone["polygon"])
        self.latest[zone["id"]] = {
            "camera_id": camera["id"],
            "zone_id": zone["id"],
            "timestamp": timestamp,
            "provenance": provenance,
            "metrics": metric,
            "risk": risk,
            "forecast": prediction,
            "inference_ms": round(latency, 2),
            "inference_fps": round(1000 / latency, 2) if latency else None,
            "pipeline_latency_ms": round((now() - timestamp) * 1000, 2),
            "queue_latency_ms": round(queue_latency, 2),
            "media_time": media_time,
            "model": model_info,
        }

    def retain(self):
        cutoff = now() - settings.evidence_retention_days * 86400
        with Session.begin() as db:
            for evidence in db.scalars(
                select(Evidence).where(Evidence.timestamp < cutoff)
            ):
                if evidence.path:
                    (RUNTIME / "evidence" / evidence.path).unlink(missing_ok=True)
                event = db.get(Event, evidence.event_id)
                if event:
                    event.evidence_refs = [
                        r for r in event.evidence_refs if r != evidence.id
                    ]
                db.delete(evidence)
            old = select(Observation.id).where(
                Observation.timestamp
                < now() - settings.observation_retention_days * 86400
            )
            db.execute(
                delete(RiskAssessment).where(RiskAssessment.observation_id.in_(old))
            )
            db.execute(
                delete(TrackMeasurement).where(TrackMeasurement.observation_id.in_(old))
            )
            db.execute(delete(Observation).where(Observation.id.in_(old)))
            db.execute(
                delete(Forecast).where(
                    Forecast.timestamp
                    < now() - settings.observation_retention_days * 86400
                )
            )

    def snapshot(self):
        with Session() as db:
            cameras = []
            for c in db.scalars(
                select(Camera)
                .where(
                    Camera.source == "synthetic"
                    if settings.synthetic_mode
                    else Camera.source != "synthetic"
                )
                .order_by(Camera.id)
            ):
                data = serialize(c)
                data["source"] = (
                    "synthetic"
                    if c.source == "synthetic"
                    else ("webcam" if c.source.startswith("webcam:") else "video")
                )
                data["health"] = (
                    "disabled"
                    if not c.enabled
                    else (
                        "synthetic"
                        if c.source == "synthetic" and settings.demo_mode
                        else c.health
                    )
                )
                if c.id in self.workers:
                    data["health"] = self.workers[c.id].health
                    worker = self.workers[c.id]
                    data["dropped_frames"] = worker.dropped
                    data["processed_frames"] = worker.processed
                    data["media_time"] = worker.media_time
                    data["media_duration"] = worker.media_duration
                    data["last_result_at"] = worker.last_result_at
                    data["detail"] = worker.detail
                data["source_metadata"] = camera_metadata(c)
                cameras.append(data)
            zones = [serialize(z) for z in db.scalars(select(Zone))]
            incidents = []
            for i, e in db.execute(
                select(Incident, Event)
                .join(Event)
                .order_by(Event.started_at.desc())
                .limit(100)
            ):
                if settings.synthetic_mode or e.provenance != "synthetic":
                    incidents.append(serialize(i) | {"event": serialize(e)})
            correlations = [
                serialize(c)
                for c in db.scalars(
                    select(Correlation)
                    .order_by(Correlation.timestamp.desc())
                    .limit(100)
                )
            ]
            visible = {c["id"] for c in cameras}
            connections = [
                serialize(c)
                for c in db.scalars(select(Connection))
                if c.camera_a in visible and c.camera_b in visible
            ]
        zones = [z for z in zones if z["camera_id"] in visible]
        incident_ids = {i["id"] for i in incidents}
        correlations = [
            c
            for c in correlations
            if c["incident_a"] in incident_ids and c["incident_b"] in incident_ids
        ]
        latest = list(self.latest.values())
        return {
            "timestamp": now(),
            "cameras": cameras,
            "zones": zones,
            "incidents": incidents,
            "correlations": correlations,
            "connections": connections,
            "latest": latest,
            "recordings": {
                "enabled": not settings.synthetic_mode,
                "context": recording_config().get("connection_context", ""),
                "model": Path(settings.model_path).name,
            },
            "history": {k: list(v) for k, v in self.histories.items()},
            "demo": {
                "enabled": settings.synthetic_mode and settings.demo_mode,
                "time": round(self.demo_time, 1),
                "duration": Scenario.duration,
                "speed": self.speed,
                "paused": self.paused,
                "phase": self.scenario.phase(self.demo_time),
            },
            "health": {
                "engine_error": self.error,
                "tick_ms": round(self.tick_ms, 2),
                "uptime_seconds": round(time.monotonic() - self.started),
            },
        }

    def reset_demo(self):
        with Session.begin() as db:
            ids = list(
                db.scalars(select(Event.id).where(Event.provenance == "synthetic"))
            )
            incidents = list(
                db.scalars(select(Incident.id).where(Incident.event_id.in_(ids)))
            )
            for e in db.scalars(select(Evidence).where(Evidence.event_id.in_(ids))):
                if e.path:
                    (RUNTIME / "evidence" / e.path).unlink(missing_ok=True)
            db.execute(
                delete(Correlation).where(
                    (Correlation.incident_a.in_(incidents))
                    | (Correlation.incident_b.in_(incidents))
                )
            )
            for cls in (Investigation, Feedback):
                db.execute(delete(cls).where(cls.incident_id.in_(incidents)))
            db.execute(delete(Incident).where(Incident.id.in_(incidents)))
            db.execute(delete(Evidence).where(Evidence.event_id.in_(ids)))
            db.execute(delete(Event).where(Event.id.in_(ids)))
            obs = select(Observation.id).where(Observation.provenance == "synthetic")
            for cls in (RiskAssessment, TrackMeasurement):
                db.execute(delete(cls).where(cls.observation_id.in_(obs)))
            db.execute(delete(Observation).where(Observation.provenance == "synthetic"))
            synthetic_cameras = list(
                db.scalars(select(Camera.id).where(Camera.source == "synthetic"))
            )
            db.execute(
                delete(Forecast).where(Forecast.camera_id.in_(synthetic_cameras))
            )
            db.add(AuditLog(action="demo_reset", subject="synthetic", data={}))
        for camera_id in synthetic_cameras:
            self.clear_camera(camera_id)
        self.demo_time = 0
        self.paused = False
        self.last_tick = time.monotonic()


engine = Engine()
