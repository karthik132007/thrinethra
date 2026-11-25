"""Browser-compatible previews of real source recordings, never generated scene content."""

import shutil
import subprocess
import threading
from pathlib import Path
from .config import RUNTIME

_preview_lock = threading.Lock()


def ensure_preview(source: Path):
    source = source.resolve()
    if not source.is_relative_to((RUNTIME / "media").resolve()) or not source.is_file():
        raise ValueError("Source must be within the configured media directory")
    stat = source.stat()
    folder = RUNTIME / "media/previews"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{source.stem}-{stat.st_size}-{stat.st_mtime_ns}.webm"
    if target.is_file():
        return target
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required for browser playback previews")
    with _preview_lock:
        if target.is_file():
            return target
        temporary = target.with_suffix(".partial.webm")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-an",
                    "-vf",
                    "scale='min(960,iw)':-2",
                    "-c:v",
                    "libvpx-vp9",
                    "-pix_fmt",
                    "yuv420p",
                    "-deadline",
                    "realtime",
                    "-cpu-used",
                    "8",
                    "-threads",
                    "2",
                    "-crf",
                    "34",
                    "-b:v",
                    "0",
                    str(temporary),
                ],
                check=True,
                timeout=120,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return target
