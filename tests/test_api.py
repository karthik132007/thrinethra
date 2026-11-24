from sqlalchemy import select
from trinethra.db import (
    Session,
    Camera,
    Zone,
    Incident,
    Event,
    Evidence,
    AuditLog,
    serialize,
)
from trinethra.engine import engine
from trinethra.config import settings
from demo.scenario import Scenario


def populate():
    with Session() as db:
        cameras = [serialize(c) for c in db.scalars(select(Camera))]
        zones = {z.camera_id: serialize(z) for z in db.scalars(select(Zone))}
    scenario = Scenario()
    for t in range(0, 76):
        for camera in cameras:
            objects = scenario.sample(camera["id"], camera["kind"], t, 1000 + t)
            engine.process(
                camera,
                zones[camera["id"]],
                objects,
                1000 + t,
                "synthetic",
                0,
                engine.synthetic_frame(camera, objects),
                t,
                0,
                engine.configuration(),
            )
    return engine.snapshot()


def test_health_and_camera_validation(client):
    assert client.get("/api/v1/health").status_code == 200
    assert len(client.get("/api/v1/cameras").json()) == 4
    data = {"name": "Bad", "lat": 17, "lon": 81, "source": "../../etc/passwd"}
    assert client.post("/api/v1/cameras", json=data).status_code == 422
    data["source"] = "rtsp://127.0.0.1/private"
    assert client.post("/api/v1/cameras", json=data).status_code == 422
    data["source"] = "synthetic"
    data["lat"] = 100
    assert client.post("/api/v1/cameras", json=data).status_code == 422


def test_upload_rejects_invalid_video(client):
    response = client.post(
        "/api/v1/streams/upload",
        files={"file": ("fake.mp4", b"not a video", "video/mp4")},
    )
    assert response.status_code == 422
    assert (
        client.post(
            "/api/v1/streams/upload", files={"file": ("shell.py", b"bad")}
        ).status_code
        == 422
    )


def test_end_to_end_demo_correlation_investigation_review_reset(client):
    data = populate()
    assert data["incidents"]
    assert data["correlations"]
    assert all(v["provenance"] == "synthetic" for v in data["latest"])
    incident = data["incidents"][0]
    id = incident["id"]
    detail = client.get(f"/api/v1/incidents/{id}").json()
    assert detail["evidence"]
    assert client.get(detail["evidence"][0]["url"]).status_code == 200
    report = client.post(
        f"/api/v1/investigations/{id}", json={"question": "What is the evidence?"}
    ).json()["data"]
    refs = {v["id"] for v in detail["evidence"]}
    assert set(report["evidence_references"]) <= refs
    assert all(set(o["evidence_references"]) <= refs for o in report["observations"])
    assert report["mode"] == "deterministic LangGraph"
    assert any("synthetic" in limit for limit in report["limitations"])
    for status in ["under_review", "verified", "resolved"]:
        response = client.patch(
            f"/api/v1/incidents/{id}/review",
            json={"status": status, "note": "Test human assessment"},
        )
        assert response.status_code == 200
    assert (
        client.get(f"/api/v1/incidents/{id}").json()["event"]["verification"]
        == "verified"
    )
    assert client.get("/api/v1/audit").json()["items"]
    assert client.post("/api/v1/demo/reset", json={}).status_code == 200
    assert not client.get("/api/v1/incidents").json()["items"]
    assert client.get("/api/v1/audit").json()["items"]


def test_settings_and_zone_validation(client):
    config = client.get("/api/v1/settings").json()["intelligence"]
    assert (
        client.put("/api/v1/settings", json=config | {"forecast_horizon": 120}).json()[
            "intelligence"
        ]["forecast_horizon"]
        == 120
    )
    assert (
        client.put(
            "/api/v1/settings", json=config | {"risk_high": 90, "risk_critical": 50}
        ).status_code
        == 422
    )
    zone = client.get("/api/v1/zones").json()[0]
    assert (
        client.put(
            "/api/v1/zones/" + zone["id"],
            json=zone | {"polygon": [[0, 0], [1, 1], [2, 2]]},
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/v1/zones/" + zone["id"], json=zone | {"capacity": 50}
        ).status_code
        == 200
    )


def test_authentication_and_session_cookie(client):
    original = settings.operator_token
    settings.operator_token = "test-secret"
    try:
        assert client.get("/api/v1/cameras").status_code == 401
        assert (
            client.post("/api/v1/auth/session", json={"token": "wrong"}).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/session", json={"token": "test-secret"}
            ).status_code
            == 200
        )
        assert client.get("/api/v1/cameras").status_code == 200
    finally:
        settings.operator_token = original


def test_automatic_resolution_and_dismissal_cooldown(client):
    data = populate()
    incident = data["incidents"][0]
    id = incident["id"]
    assert (
        client.patch(
            f"/api/v1/incidents/{id}/review",
            json={"status": "dismissed", "note": "False positive"},
        ).status_code
        == 200
    )
    assert (
        client.get(f"/api/v1/incidents/{id}").json()["event"]["verification"]
        == "dismissed"
    )
    with Session() as db:
        camera = serialize(db.get(Camera, "cam-01"))
        zone = serialize(db.scalar(select(Zone).where(Zone.camera_id == "cam-01")))
    for t in range(1080, 1100):
        engine.process(
            camera,
            zone,
            [],
            t,
            "synthetic",
            0,
            engine.synthetic_frame(camera, []),
            t,
            0,
            engine.configuration(),
        )
    with Session() as db:
        events = list(db.scalars(select(Event).where(Event.camera_id == "cam-01")))
        assert all(e.status in ["resolved", "dismissed"] for e in events)


def test_websocket_snapshot(client):
    with client.websocket_connect("/ws/live") as socket:
        socket.send_json({"token": ""})
        assert socket.receive_json()["type"] == "snapshot"


def test_grounding_matches_retained_snapshot_and_missing_evidence(client):
    data = populate()
    id = data["incidents"][0]["id"]
    detail = client.get(f"/api/v1/incidents/{id}").json()
    report = client.post(f"/api/v1/investigations/{id}", json={}).json()["data"]
    last = detail["evidence"][-1]
    assert [o["claim"] for o in report["observations"]] == last["data"]["factors"]
    assert all(o["evidence_references"] == [last["id"]] for o in report["observations"])
    with Session.begin() as db:
        for row in db.scalars(
            select(Evidence).where(Evidence.event_id == detail["event"]["id"])
        ):
            db.delete(row)
    report = client.post(f"/api/v1/investigations/{id}", json={}).json()["data"]
    assert report["observations"] == []
    assert report["evidence_references"] == []
    assert any("unavailable" in value for value in report["limitations"])


def test_disabled_stream_and_source_reconfiguration_clear_history(client):
    populate()
    assert engine.latest
    assert client.post("/api/v1/streams/cam-01/stop", json={}).status_code == 200
    camera = client.get("/api/v1/cameras").json()[0]
    assert not camera["enabled"]
    body = {k: camera[k] for k in ("name", "lat", "lon", "kind", "enabled")}
    body |= {"source": "synthetic", "enabled": True}
    assert client.put("/api/v1/cameras/cam-01", json=body).status_code == 200
    assert not any(v["camera_id"] == "cam-01" for v in engine.latest.values())
    assert "zone-east" not in engine.histories


def test_retention_removes_expired_evidence_and_references(client):
    populate()
    with Session() as db:
        paths = [e.path for e in db.scalars(select(Evidence))]
    engine.retain()
    with Session() as db:
        assert not list(db.scalars(select(Evidence)))
        assert all(not e.evidence_refs for e in db.scalars(select(Event)))
    from trinethra.config import RUNTIME

    assert all(not (RUNTIME / "evidence" / p).exists() for p in paths)
