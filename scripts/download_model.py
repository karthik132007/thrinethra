"""Explicit download; never silently download weights during a live inference request."""

import hashlib
import urllib.request
from pathlib import Path

url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
path = Path(__file__).resolve().parents[1] / "runtime/models/yolo11n.pt"
path.parent.mkdir(parents=True, exist_ok=True)
if not path.exists():
    temporary = path.with_suffix(".download")
    with (
        urllib.request.urlopen(url, timeout=60) as response,
        temporary.open("wb") as output,
    ):
        import shutil

        shutil.copyfileobj(response, output)
    temporary.replace(path)
print(f"{path}: {hashlib.sha256(path.read_bytes()).hexdigest()}")
print(
    "Model: Ultralytics YOLO11n, AGPL-3.0. Review upstream license before other distribution models."
)
