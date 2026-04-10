import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    token: str
    default_interval: int
    data_dir: Path
    lists_dir: Path
    state_file: Path


def load_settings() -> Settings:
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    lists_dir = Path(os.getenv("LISTS_DIR", str(data_dir / "lists")))
    state_file = Path(os.getenv("STATE_FILE", str(data_dir / "state.json")))

    return Settings(
        token=os.getenv("TOKEN", ""),
        default_interval=int(os.getenv("INTERVAL", "3600")),
        data_dir=data_dir,
        lists_dir=lists_dir,
        state_file=state_file,
    )
