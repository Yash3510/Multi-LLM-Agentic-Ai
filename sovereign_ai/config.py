from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path
    storage_dir: Path
    local_model_url: str
    default_model: str


def load_settings() -> Settings:
    data_dir = Path(os.getenv("SOVEREIGN_DATA_DIR", "./data")).expanduser()
    return Settings(
        data_dir=data_dir,
        db_path=data_dir / "sovereign.db",
        storage_dir=data_dir / "files",
        local_model_url=os.getenv("LOCAL_MODEL_URL", "http://localhost:1234/v1"),
        default_model=os.getenv("LOCAL_MODEL", os.getenv("OLLAMA_MODEL", "local-model")),
    )
