from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    create_engine,
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Text,
    Index,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).timestamp()


class Base(DeclarativeBase):
    pass


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(Text, default="synthetic")
    kind: Mapped[str] = mapped_column(String, default="crowd")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health: Mapped[str] = mapped_column(String, default="idle")
    detail: Mapped[str] = mapped_column(String, default="")


class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer, default=40)
    polygon: Mapped[list] = mapped_column(
        JSON, default=lambda: [[0.05, 0.1], [0.95, 0.1], [0.95, 0.95], [0.05, 0.95]]
    )
    restricted: Mapped[bool] = mapped_column(Boolean, default=False)


class Connection(Base):
    __tablename__ = "camera_connections"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    camera_a: Mapped[str] = mapped_column(ForeignKey("cameras.id"), index=True)
    camera_b: Mapped[str] = mapped_column(ForeignKey("cameras.id"), index=True)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"))
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    timestamp: Mapped[float] = mapped_column(Float)
    provenance: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (Index("ix_observation_camera_time", "camera_id", "timestamp"),)


class TrackMeasurement(Base):
    __tablename__ = "track_measurements"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[dict] = mapped_column(JSON)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"), index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    type: Mapped[str] = mapped_column(String)
    started_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="active", index=True)
    verification: Mapped[str] = mapped_column(String, default="unverified")
    provenance: Mapped[str] = mapped_column(String)
    factors: Mapped[list] = mapped_column(JSON)
    tracks: Mapped[list] = mapped_column(JSON)
    evidence_refs: Mapped[list] = mapped_column(JSON)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), unique=True)
    title: Mapped[str] = mapped_column(String)
    timeline: Mapped[list] = mapped_column(JSON, default=list)


class Correlation(Base):
    __tablename__ = "incident_correlations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    incident_a: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    incident_b: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[float] = mapped_column(Float)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String)
    components: Mapped[dict] = mapped_column(JSON)


class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"), index=True)
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    data: Mapped[dict] = mapped_column(JSON)


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), index=True)
    observation_id: Mapped[str | None] = mapped_column(
        ForeignKey("observations.id", ondelete="SET NULL"), nullable=True
    )
    timestamp: Mapped[float] = mapped_column(Float, index=True)
    path: Mapped[str | None] = mapped_column(String, nullable=True)
    provenance: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)


class Investigation(Base):
    __tablename__ = "investigation_reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    timestamp: Mapped[float] = mapped_column(Float)
    data: Mapped[dict] = mapped_column(JSON)


class Feedback(Base):
    __tablename__ = "operator_feedback"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    timestamp: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(Text)


class Configuration(Base):
    __tablename__ = "application_configuration"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    timestamp: Mapped[float] = mapped_column(Float, default=now, index=True)
    action: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON, default=dict)


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30}
    if settings.database_url.startswith("sqlite")
    else {},
)
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_pragmas(dbapi, _):
        dbapi.execute("PRAGMA foreign_keys=ON")
        dbapi.execute("PRAGMA journal_mode=WAL")


Session = sessionmaker(engine, expire_on_commit=False)


def serialize(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
