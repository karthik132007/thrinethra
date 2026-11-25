from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")
    runtime_dir: str = "runtime"
    database_url: str = "sqlite:///runtime/trinethra.db"
    operator_token: str = ""
    cookie_secure: bool = False
    demo_mode: bool = True
    synthetic_mode: bool = False
    torch_threads: int = 2
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    model_path: str = "runtime/models/yolo11n.pt"
    device: str = "cpu"
    sample_fps: float = 2
    inference_size: int = 960
    evidence_retention_days: int = 7
    observation_retention_days: int = 7
    blur_evidence: bool = True
    allow_network_streams: bool = False
    llm_provider: str = "ollama"
    llm_base_url: str = "http://127.0.0.1:11435"
    llm_model: str = "qwen2.5:1.5b"
    llm_api_key: str = ""


settings = Settings()
RUNTIME = ROOT / settings.runtime_dir
for folder in ("media", "evidence", "models"):
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)
