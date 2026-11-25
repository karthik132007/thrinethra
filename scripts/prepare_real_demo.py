"""Seed real recording cameras without deleting existing sources or incident history."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path[:0] = [str(ROOT), str(ROOT / "apps/backend")]
os.environ["SYNTHETIC_MODE"] = "false"
from trinethra.db import Base, engine as database, Session, Camera
from sqlalchemy import select
from trinethra.engine import engine
from trinethra.assets import recording_config
from trinethra.config import RUNTIME


def main():
    for camera in recording_config()["cameras"]:
        source = RUNTIME / "media" / camera["source"].removeprefix("media:")
        if not source.is_file():
            raise SystemExit("Real footage missing. Run make assets first.")
    Base.metadata.create_all(database)
    engine.seed()
    with Session() as db:
        for camera in db.scalars(select(Camera).where(Camera.source != "synthetic")):
            print(f"{camera.id}: {camera.name}")
    print(
        "Real sources ready; all displayed measurements will come from detector inference. Old synthetic sources are disabled."
    )


if __name__ == "__main__":
    main()
