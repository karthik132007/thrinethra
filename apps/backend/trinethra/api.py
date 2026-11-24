import asyncio
import contextlib
import hmac
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
import psutil
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, or_, func
from .config import ROOT, RUNTIME, settings
from .db import (
    Base,
    engine as database,
    Session,
    Camera,
    Zone,
    Connection,
    Observation,
    Event,
    Incident,
    Correlation,
    Evidence,
    Investigation,
    Feedback,
    Configuration,
    AuditLog,
    RiskAssessment,
    Forecast,
    serialize,
    now,
    uid,
)
from .engine import engine
from packages.intelligence.analytics import DEFAULTS
from packages.investigation.agent import investigate

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("trinethra.api")


@asynccontextmanager
async def lifespan(app):
    if not settings.demo_mode and not settings.operator_token:
        raise RuntimeError("Set OPERATOR_TOKEN when DEMO_MODE=false")
    Base.metadata.create_all(database)
    engine.running = True
    task = asyncio.create_task(engine.loop())
    yield
    engine.running = False
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    for worker in engine.workers.values():
        worker.stop()


app = FastAPI(
    title="Trinethra Situational Intelligence", version="0.1.0", lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)
limits = defaultdict(deque)
bearer = HTTPBearer(auto_error=False)
process_monitor = psutil.Process()
process_monitor.cpu_percent()


def valid_token(token):
    return (not settings.operator_token and settings.demo_mode) or hmac.compare_digest(
        token, settings.operator_token
    )


async def operator(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
):
    token = (credentials.credentials if credentials else "") or request.cookies.get(
        "trinethra_operator", ""
    )
    if not valid_token(token):
        raise HTTPException(401, "Operator authentication required")


@app.middleware("http")
async def middleware(request, call_next):
    started = time.perf_counter()
    key = (request.client.host, request.url.path)
    if request.method != "GET":
        bucket = limits[key]
        stamp = time.monotonic()
        while bucket and stamp - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 30:
            return Response("Rate limit exceeded", 429)
        bucket.append(stamp)
        # Bound the number of tracked clients as well as each client's request history.
        if len(limits) > 4096:
            limits.clear()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    log.info(
        json.dumps(
            {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        )
    )
    return response


class Login(BaseModel):
    token: str = Field(max_length=512)


@app.post("/api/v1/auth/session")
async def login(body: Login, response: Response):
    if not valid_token(body.token):
        raise HTTPException(401, "Invalid operator token")
    response.set_cookie(
        "trinethra_operator",
        body.token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=28800,
    )
    return {"authenticated": True}


AUTH = [Depends(operator)]


def audit(db, action, subject, data=None):
    db.add(AuditLog(action=action, subject=subject, data=data or {}))


def require(db, cls, id):
    row = db.get(cls, id)
    if row is None:
        raise HTTPException(404, f"{cls.__name__} not found")
    return row


def camera_public(c):
    data = serialize(c)
    data["source"] = (
        "synthetic"
        if c.source == "synthetic"
        else ("webcam" if c.source.startswith("webcam:") else "video")
    )
    return data


def source_path(source):
    if source == "synthetic":
        if not settings.demo_mode:
            raise HTTPException(422, "Synthetic sources require DEMO_MODE=true")
        return source
    if source.startswith("webcam:") and source.split(":")[1].isdigit():
        return source
    if source.startswith("rtsp://"):
        if not settings.allow_network_streams:
            raise HTTPException(
                422, "Network streams disabled; enable ALLOW_NETWORK_STREAMS explicitly"
            )
        if not urlparse(source).hostname:
            raise HTTPException(422, "Invalid RTSP URL")
        return source
    relative = source.removeprefix("media:")
    candidate = (RUNTIME / "media" / relative).resolve()
    if (
        not candidate.is_relative_to((RUNTIME / "media").resolve())
        or not candidate.is_file()
    ):
        raise HTTPException(
            422, "Source must be an uploaded file, webcam:N, or explicitly enabled RTSP"
        )
    return str(candidate)


class CameraInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    source: str = Field(default="synthetic", max_length=1000)
    kind: Literal["crowd", "road"] = "crowd"
    enabled: bool = True


class ZoneInput(BaseModel):
    camera_id: str
    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(ge=1, le=100000)
    polygon: list[list[float]] = Field(min_length=3, max_length=30)
    restricted: bool = False

    @model_validator(mode="after")
    def polygon_valid(self):
        if any(len(p) != 2 or any(not 0 <= v <= 1 for v in p) for p in self.polygon):
            raise ValueError("Polygon requires normalized [x,y] coordinates in [0,1]")
        import cv2, numpy as np

        if abs(cv2.contourArea(np.array(self.polygon, dtype=np.float32))) < 0.001:
            raise ValueError("Polygon must have nonzero area")
        return self


class Review(BaseModel):
    status: Literal["under_review", "verified", "dismissed", "resolved"]
    note: str = Field(default="", max_length=2000)


class Question(BaseModel):
    question: str = Field(default="", max_length=500)


class DemoControl(BaseModel):
    paused: bool | None = None
    speed: float | None = Field(default=None, ge=0.25, le=10)


class IntelligenceSettings(BaseModel):
    persistence_seconds: float = Field(default=6, ge=2, le=120)
    occupancy_threshold: float = Field(default=0.8, ge=0.2, le=2)
    stationary_seconds: float = Field(default=8, ge=2, le=120)
    forecast_horizon: int = Field(default=60, ge=10, le=600)
    risk_high: float = Field(default=50, ge=25, le=90)
    risk_critical: float = Field(default=75, ge=30, le=100)
    cooldown_seconds: float = Field(default=30, ge=5, le=600)
    confidence_threshold: float = Field(default=0.3, ge=0.1, le=0.95)

    @model_validator(mode="after")
    def levels(self):
        if self.risk_high >= self.risk_critical:
            raise ValueError("Critical risk must exceed high risk")
        return self


@app.get("/api/v1/health", dependencies=AUTH)
async def health():
    process = process_monitor
    return {
        "status": "degraded" if engine.error else "ok",
        "database": "connected",
        "demo_mode": settings.demo_mode,
        "model_available": (ROOT / settings.model_path).is_file(),
        "device": settings.device,
        "memory_mb": round(process.memory_info().rss / 1024**2, 1),
        "process_cpu_percent": process.cpu_percent(),
        "system_cpu_percent": psutil.cpu_percent(),
        "sample_fps": settings.sample_fps,
        "inference_size": settings.inference_size,
        "gpu": "not measured",
        "workers": {
            id: {"health": w.health, "detail": w.detail, "dropped_frames": w.dropped}
            for id, w in engine.workers.items()
        },
        "retention": {
            "evidence_days": settings.evidence_retention_days,
            "observations_days": settings.observation_retention_days,
        },
        "authentication": "token"
        if settings.operator_token
        else "local demo without token",
        "tick_ms": round(engine.tick_ms, 2),
        "engine_error": engine.error,
    }


@app.get("/api/v1/snapshot", dependencies=AUTH)
async def snapshot():
    return engine.snapshot()


@app.get("/api/v1/cameras", dependencies=AUTH)
async def cameras():
    return engine.snapshot()["cameras"]


@app.post("/api/v1/cameras", dependencies=AUTH, status_code=201)
async def create_camera(body: CameraInput):
    source = source_path(body.source)
    with Session.begin() as db:
        camera = Camera(**(body.model_dump() | {"source": source}))
        db.add(camera)
        db.flush()
        zone = Zone(
            camera_id=camera.id,
            name=body.name + " zone",
            capacity=16 if body.kind == "road" else 40,
        )
        db.add(zone)
        audit(db, "camera_created", camera.id)
        result = camera_public(camera)
    if body.enabled and source != "synthetic":
        engine.start_worker(serialize(camera))
    return result


@app.put("/api/v1/cameras/{camera_id}", dependencies=AUTH)
async def update_camera(camera_id: str, body: CameraInput):
    source = source_path(body.source)
    with Session.begin() as db:
        camera = require(db, Camera, camera_id)
        for key, value in (body.model_dump() | {"source": source}).items():
            setattr(camera, key, value)
        camera.health = "idle"
        camera.detail = ""
        audit(db, "camera_updated", camera_id)
        result = serialize(camera)
        # Resolve old source events before changing provenance/history.
        for event in db.scalars(
            select(Event).where(
                Event.camera_id == camera_id,
                Event.status.in_(["active", "escalated", "under_review", "verified"]),
            )
        ):
            event.status = "resolved"
            event.updated_at = now()
            incident = db.scalar(select(Incident).where(Incident.event_id == event.id))
            incident.timeline = incident.timeline + [
                {
                    "timestamp": now(),
                    "status": "resolved",
                    "note": "Camera source/configuration changed",
                }
            ]
    engine.stop_worker(camera_id)
    engine.clear_camera(camera_id)
    if body.enabled and source != "synthetic":
        engine.start_worker(result)
    return camera_public(camera)


@app.get("/api/v1/zones", dependencies=AUTH)
async def zones():
    return engine.snapshot()["zones"]


@app.post("/api/v1/zones", dependencies=AUTH, status_code=201)
async def add_zone(body: ZoneInput):
    with Session.begin() as db:
        require(db, Camera, body.camera_id)
        row = Zone(**body.model_dump())
        db.add(row)
        db.flush()
        audit(db, "zone_created", row.id)
        return serialize(row)


@app.put("/api/v1/zones/{zone_id}", dependencies=AUTH)
async def update_zone(zone_id: str, body: ZoneInput):
    with Session.begin() as db:
        zone = require(db, Zone, zone_id)
        if zone.camera_id != body.camera_id:
            raise HTTPException(422, "A zone cannot move to another camera")
        for key, value in body.model_dump().items():
            setattr(zone, key, value)
        audit(db, "zone_updated", zone_id)
    engine.clear_camera(body.camera_id)
    return serialize(zone)


@app.get("/api/v1/connections", dependencies=AUTH)
async def connections():
    return engine.snapshot()["connections"]


class ConnectionInput(BaseModel):
    camera_a: str
    camera_b: str


@app.post("/api/v1/connections", dependencies=AUTH, status_code=201)
async def add_connection(body: ConnectionInput):
    if body.camera_a == body.camera_b:
        raise HTTPException(422, "Connect two different cameras")
    with Session.begin() as db:
        require(db, Camera, body.camera_a)
        require(db, Camera, body.camera_b)
        row = Connection(**body.model_dump())
        db.add(row)
        db.flush()
        audit(db, "connection_created", row.id)
        return serialize(row)


@app.post("/api/v1/streams/upload", dependencies=AUTH, status_code=201)
async def upload(file: UploadFile):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise HTTPException(422, "Supported video formats: mp4, avi, mov, mkv, webm")
    name = uid() + extension
    path = RUNTIME / "media" / name
    size = 0
    try:
        with path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 250 * 1024 * 1024:
                    raise HTTPException(413, "Maximum upload size is 250 MiB")
                output.write(chunk)
        import cv2

        capture = cv2.VideoCapture(str(path))
        ok, _ = capture.read()
        capture.release()
        if not ok:
            raise HTTPException(422, "Uploaded file is not a decodable video")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    with Session.begin() as db:
        audit(db, "media_uploaded", name, {"bytes": size})
    return {"source": "media:" + name, "bytes": size, "filename": file.filename}


@app.post("/api/v1/streams/{camera_id}/{action}", dependencies=AUTH)
async def stream_control(camera_id: str, action: Literal["start", "stop"]):
    with Session.begin() as db:
        camera = require(db, Camera, camera_id)
        camera.enabled = action == "start"
        camera.health = "idle" if camera.enabled else "stopped"
        audit(db, "stream_" + action, camera_id)
        data = serialize(camera)
    engine.stop_worker(camera_id)
    if action == "start" and data["source"] != "synthetic":
        engine.start_worker(data)
    return {"camera_id": camera_id, "enabled": data["enabled"]}


@app.get("/api/v1/streams/{camera_id}/frame", dependencies=AUTH)
async def frame(camera_id: str):
    content = engine.frames.get(camera_id)
    if content is None:
        raise HTTPException(404, "No frame available yet")
    return Response(content, media_type="image/jpeg")


@app.get("/api/v1/observations", dependencies=AUTH)
async def observations(
    camera_id: str | None = None,
    zone_id: str | None = None,
    since: float = 0,
    limit: int = 100,
    offset: int = 0,
):
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    with Session() as db:
        query = select(Observation).where(Observation.timestamp >= since)
        if camera_id:
            query = query.where(Observation.camera_id == camera_id)
        if zone_id:
            query = query.where(Observation.zone_id == zone_id)
        return {
            "items": [
                serialize(row)
                for row in db.scalars(
                    query.order_by(Observation.timestamp.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ],
            "limit": limit,
            "offset": offset,
        }


@app.get("/api/v1/events", dependencies=AUTH)
async def events(status: str | None = None, limit: int = 100, offset: int = 0):
    with Session() as db:
        query = select(Event)
        if status:
            query = query.where(Event.status == status)
        return {
            "items": [
                serialize(row)
                for row in db.scalars(
                    query.order_by(Event.started_at.desc())
                    .limit(max(1, min(limit, 500)))
                    .offset(max(offset, 0))
                )
            ]
        }


@app.get("/api/v1/incidents", dependencies=AUTH)
async def incidents(
    severity: str | None = None,
    status: str | None = None,
    q: str = "",
    limit: int = 100,
    offset: int = 0,
):
    with Session() as db:
        query = select(Incident, Event).join(Event)
        if severity:
            query = query.where(Event.severity == severity)
        if status:
            query = query.where(Event.status == status)
        if q:
            query = query.where(Incident.title.ilike("%" + q[:100] + "%"))
        rows = db.execute(
            query.order_by(Event.started_at.desc())
            .limit(max(1, min(limit, 500)))
            .offset(max(offset, 0))
        )
        return {"items": [serialize(i) | {"event": serialize(e)} for i, e in rows]}


@app.get("/api/v1/incidents/{incident_id}", dependencies=AUTH)
async def incident_details(incident_id: str):
    with Session() as db:
        incident = require(db, Incident, incident_id)
        event = require(db, Event, incident.event_id)
        evidence = [
            serialize(e) | {"url": f"/api/v1/evidence/{e.id}/frame"}
            for e in db.scalars(
                select(Evidence)
                .where(Evidence.event_id == event.id)
                .order_by(Evidence.timestamp)
            )
        ]
        reports = [
            serialize(r)
            for r in db.scalars(
                select(Investigation)
                .where(Investigation.incident_id == incident_id)
                .order_by(Investigation.timestamp.desc())
                .limit(10)
            )
        ]
        feedback = [
            serialize(r)
            for r in db.scalars(
                select(Feedback).where(Feedback.incident_id == incident_id)
            )
        ]
        return serialize(incident) | {
            "event": serialize(event),
            "evidence": evidence,
            "reports": reports,
            "feedback": feedback,
        }


@app.patch("/api/v1/incidents/{incident_id}/review", dependencies=AUTH)
async def review(incident_id: str, body: Review):
    with Session.begin() as db:
        incident = require(db, Incident, incident_id)
        event = require(db, Event, incident.event_id)
        if event.status in {"resolved", "dismissed"} and body.status == "under_review":
            raise HTTPException(409, "Closed incident cannot be reopened")
        event.status = body.status
        if body.status in {"verified", "dismissed"}:
            event.verification = body.status
        incident.timeline = incident.timeline + [
            {
                "timestamp": now(),
                "status": body.status,
                "note": body.note or "Operator review",
            }
        ]
        db.add(
            Feedback(
                incident_id=incident_id,
                timestamp=now(),
                verdict=body.status,
                note=body.note,
            )
        )
        audit(db, "operator_review", incident_id, body.model_dump())
    return await incident_details(incident_id)


@app.get("/api/v1/evidence/{evidence_id}/frame", dependencies=AUTH)
async def evidence_frame(evidence_id: str):
    with Session() as db:
        row = require(db, Evidence, evidence_id)
        path = RUNTIME / "evidence" / (row.path or "missing")
        if not path.is_file():
            raise HTTPException(410, "Evidence has expired or is unavailable")
        return FileResponse(path, media_type="image/jpeg")


@app.get("/api/v1/correlations", dependencies=AUTH)
async def correlations():
    return engine.snapshot()["correlations"]


@app.get("/api/v1/forecasts", dependencies=AUTH)
async def forecasts():
    return [
        {"camera_id": v["camera_id"], "zone_id": v["zone_id"], **v["forecast"]}
        for v in engine.latest.values()
    ]


@app.get("/api/v1/investigations", dependencies=AUTH)
async def reports(limit: int = 50, offset: int = 0):
    with Session() as db:
        return {
            "items": [
                serialize(r)
                for r in db.scalars(
                    select(Investigation)
                    .order_by(Investigation.timestamp.desc())
                    .limit(max(1, min(100, limit)))
                    .offset(max(0, offset))
                )
            ]
        }


@app.post("/api/v1/investigations/{incident_id}", dependencies=AUTH)
async def investigation(incident_id: str, body: Question):
    with Session() as db:
        i = require(db, Incident, incident_id)
        e = require(db, Event, i.event_id)
        c = require(db, Camera, e.camera_id)
        z = require(db, Zone, e.zone_id)
        evidence = [
            serialize(v)
            for v in db.scalars(
                select(Evidence)
                .where(Evidence.event_id == e.id)
                .order_by(Evidence.timestamp)
            )
        ]
        related = [
            serialize(v)
            for v in db.scalars(
                select(Correlation).where(
                    or_(
                        Correlation.incident_a == incident_id,
                        Correlation.incident_b == incident_id,
                    )
                )
            )
        ]
        historical = [
            serialize(v)
            for v in db.scalars(
                select(Observation)
                .where(
                    Observation.camera_id == c.id,
                    Observation.timestamp >= e.started_at - 60,
                    Observation.timestamp <= e.updated_at,
                )
                .order_by(Observation.timestamp.desc())
                .limit(60)
            )
        ]
        risk = evidence[-1]["data"].get("risk") if evidence else None
        forecast_row = db.scalar(
            select(Forecast)
            .where(Forecast.camera_id == c.id, Forecast.timestamp <= e.updated_at)
            .order_by(Forecast.timestamp.desc())
        )
        context = {
            "incident": serialize(i),
            "event": serialize(e),
            "camera": camera_public(c),
            "zone": serialize(z),
            "evidence": evidence,
            "related": related,
            "history": historical,
            "risk": risk,
            "forecast": forecast_row.data if forecast_row else None,
            "references": [
                json.loads((ROOT / "configs/safety-reference.json").read_text())
            ],
        }
    data = await investigate(
        context,
        body.question,
        settings.llm_provider,
        settings.llm_base_url,
        settings.llm_model,
        settings.llm_api_key,
    )
    with Session.begin() as db:
        row = Investigation(incident_id=incident_id, timestamp=now(), data=data)
        db.add(row)
        db.flush()
        audit(db, "investigation_created", incident_id, {"mode": data["mode"]})
        return serialize(row)


@app.get("/api/v1/settings", dependencies=AUTH)
async def get_settings():
    return {
        "intelligence": engine.configuration(),
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "configured_by": "environment variables",
        },
        "privacy": {
            "blur_evidence": settings.blur_evidence,
            "evidence_retention_days": settings.evidence_retention_days,
            "observation_retention_days": settings.observation_retention_days,
        },
        "device": settings.device,
    }


@app.put("/api/v1/settings", dependencies=AUTH)
async def save_settings(body: IntelligenceSettings):
    with Session.begin() as db:
        row = db.get(Configuration, "intelligence")
        if row:
            row.data = body.model_dump()
        else:
            db.add(Configuration(id="intelligence", data=body.model_dump()))
        audit(db, "settings_updated", "intelligence", body.model_dump())
    return await get_settings()


@app.get("/api/v1/audit", dependencies=AUTH)
async def audit_logs(limit: int = 100, offset: int = 0):
    with Session() as db:
        return {
            "items": [
                serialize(r)
                for r in db.scalars(
                    select(AuditLog)
                    .order_by(AuditLog.timestamp.desc())
                    .limit(max(1, min(500, limit)))
                    .offset(max(0, offset))
                )
            ]
        }


@app.post("/api/v1/demo/control", dependencies=AUTH)
async def demo_control(body: DemoControl):
    if not settings.demo_mode:
        raise HTTPException(409, "Demo mode is disabled")
    if body.paused is not None:
        engine.paused = body.paused
    if body.speed is not None:
        engine.speed = body.speed
    return engine.snapshot()["demo"]


@app.post("/api/v1/demo/reset", dependencies=AUTH)
async def demo_reset():
    if not settings.demo_mode:
        raise HTTPException(409, "Demo mode is disabled")
    engine.reset_demo()
    return {"reset": True, "scope": "synthetic data only"}


@app.websocket("/ws/live")
async def live(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.cors_origins.split(","):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5)
        if not valid_token(
            message.get("token", "") or websocket.cookies.get("trinethra_operator", "")
        ):
            await websocket.close(code=1008)
            return
        while True:
            await websocket.send_json({"type": "snapshot", "data": engine.snapshot()})
            await asyncio.sleep(1)
    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
        pass
