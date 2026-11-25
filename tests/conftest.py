import os
from pathlib import Path
from uuid import uuid4

os.environ["DATABASE_URL"] = f"sqlite:////tmp/trinethra-test-{uuid4().hex}.db"
os.environ["RUNTIME_DIR"] = f"/tmp/trinethra-test-media-{uuid4().hex}"
os.environ["LLM_PROVIDER"] = "none"
os.environ["OPERATOR_TOKEN"] = ""
os.environ["DEMO_MODE"] = "true"
os.environ["SYNTHETIC_MODE"] = "true"
import pytest
from trinethra.db import Base, engine as database, Session
from trinethra.engine import engine
from packages.intelligence.analytics import Analytics
from demo.scenario import Scenario


@pytest.fixture(autouse=True)
def clean_store():
    Base.metadata.create_all(database)
    with Session.begin() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    engine.latest.clear()
    engine.histories.clear()
    engine.frames.clear()
    engine.analytics = Analytics()
    engine.scenario = Scenario()
    engine.workers.clear()
    engine.paused = True
    engine.seed()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from trinethra.api import app

    return TestClient(app)
