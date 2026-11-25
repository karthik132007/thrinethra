"""Publisher/source metadata. This config describes inputs, never inference outputs."""

import json
import hashlib
from functools import lru_cache
from pathlib import Path
import yaml
from .config import ROOT, RUNTIME


@lru_cache(maxsize=1)
def manifest():
    return json.loads((ROOT / "configs/assets.json").read_text())


@lru_cache(maxsize=1)
def recording_config():
    return yaml.safe_load((ROOT / "configs/cameras.real.yaml").read_text())


@lru_cache(maxsize=64)
def verified_asset(source, modified, size):
    asset = next(
        (
            row
            for row in manifest()["assets"]
            if row["kind"] == "video" and Path(row["path"]).name == Path(source).name
        ),
        None,
    )
    if not asset:
        return None
    digest = hashlib.sha256()
    with Path(source).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return asset if digest.hexdigest() == asset["sha256"] else None


def camera_metadata(camera):
    source = camera["source"] if isinstance(camera, dict) else camera.source
    id = camera["id"] if isinstance(camera, dict) else camera.id
    entry = next(
        (
            row
            for row in recording_config()["cameras"]
            if row["id"] == id
            and source
            == str((RUNTIME / "media" / row["source"].removeprefix("media:")).resolve())
        ),
        None,
    )
    path = Path(source)
    stat = path.stat() if path.is_file() else None
    asset = verified_asset(source, stat.st_mtime_ns, stat.st_size) if stat else None
    return {
        "title": asset["id"]
        if asset
        else ("synthetic" if source == "synthetic" else "operator supplied"),
        "publisher_url": asset["url"] if asset else None,
        "sha256": asset.get("sha256") if asset else None,
        "recorded": bool(asset),
        "location_verified": False,
        "crop": entry.get("crop") if entry else None,
        "recording_group": entry.get("recording_group") if entry else (asset.get("recording_group") if asset else None),
        "context": asset.get("context", "Recorded video; geographic location not configured. Layout markers are not GPS evidence.")
        if asset
        else "Operator-configured source; verify location before regional interpretation.",
    }
