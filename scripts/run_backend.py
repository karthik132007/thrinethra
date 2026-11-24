import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root)
sys.path[:0] = [str(root), str(root / "apps/backend")]
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "trinethra.api:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
    )
