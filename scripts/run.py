"""Start the local real-inference application and optional local LLM together."""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reachable(url):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    children = []

    def start(command, env=None):
        child = subprocess.Popen(
            command, cwd=ROOT, env=env or os.environ.copy(), start_new_session=True
        )
        children.append(child)
        return child

    def stop(*_, exit_code=0):
        for child in reversed(children):
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        raise SystemExit(exit_code)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    sys.path.insert(0, str(ROOT / "apps/backend"))
    from trinethra.config import settings

    if not settings.synthetic_mode and not (ROOT / settings.model_path).is_file():
        raise SystemExit("Detector weights missing. Run make setup first.")
    if settings.llm_provider == "ollama" and not reachable(
        settings.llm_base_url + "/api/tags"
    ):
        if not shutil.which("ollama"):
            print(
                "Ollama not installed; measured evidence remains available. Install Ollama and run make llm-model.",
                flush=True,
            )
        else:
            env = os.environ.copy()
            env.update(
                OLLAMA_HOST=settings.llm_base_url.removeprefix("http://"),
                OLLAMA_MODELS=str(ROOT / "runtime/models/ollama"),
                OLLAMA_NO_CLOUD="1",
            )
            start(["ollama", "serve"], env)
    try:
        start([str(ROOT / ".venv/bin/python"), "scripts/run_backend.py"])
        start(
            [
                "npm",
                "--prefix",
                "apps/frontend",
                "run",
                "start" if args.production else "dev",
            ]
        )
        print(
            "Trinethra: http://127.0.0.1:3000 | API: http://127.0.0.1:8000/docs",
            flush=True,
        )
        while True:
            time.sleep(0.5)
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError(
                        f"Child service exited with {child.returncode}; check output above."
                    )
    except KeyboardInterrupt:
        stop()
    except Exception as exc:
        print(str(exc), file=sys.stderr, flush=True)
        stop(exit_code=1)


if __name__ == "__main__":
    main()
