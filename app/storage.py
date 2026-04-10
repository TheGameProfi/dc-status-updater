import json
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock


LIST_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class QuoteRepository:
    def __init__(self, lists_dir: Path) -> None:
        self._lists_dir = lists_dir
        self._lock = Lock()

    def ensure_initialized(self) -> None:
        self._lists_dir.mkdir(parents=True, exist_ok=True)
        if self.list_names():
            return
        self._list_path("default").write_text("", encoding="utf-8")

    def list_names(self) -> list[str]:
        self._lists_dir.mkdir(parents=True, exist_ok=True)
        names = [p.stem for p in self._lists_dir.glob("*.txt") if p.is_file()]
        return sorted(names)

    def create_list(self, name: str) -> None:
        validated = self._validate_list_name(name)
        path = self._list_path(validated)
        with self._lock:
            if path.exists():
                raise ValueError(f"List '{validated}' already exists.")
            path.write_text("", encoding="utf-8")

    def delete_list(self, name: str) -> None:
        validated = self._validate_list_name(name)
        path = self._list_path(validated)
        with self._lock:
            if not path.exists():
                raise FileNotFoundError(f"List '{validated}' does not exist.")
            path.unlink()

    def get_quotes(self, name: str) -> list[str]:
        validated = self._validate_list_name(name)
        path = self._list_path(validated)
        if not path.exists():
            raise FileNotFoundError(f"List '{validated}' does not exist.")
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def add_quote(self, name: str, text: str) -> None:
        validated = self._validate_list_name(name)
        clean = text.strip()
        if not clean:
            raise ValueError("Quote must not be empty.")
        path = self._list_path(validated)
        if not path.exists():
            raise FileNotFoundError(f"List '{validated}' does not exist.")

        with self._lock:
            with path.open("a", encoding="utf-8") as fp:
                fp.write(clean + "\n")

    def remove_quote(self, name: str, index: int) -> None:
        validated = self._validate_list_name(name)
        path = self._list_path(validated)
        if not path.exists():
            raise FileNotFoundError(f"List '{validated}' does not exist.")

        with self._lock:
            quotes = self.get_quotes(validated)
            if index >= len(quotes):
                raise IndexError("Quote index out of range.")
            quotes.pop(index)
            payload = "".join(f"{quote}\n" for quote in quotes)
            path.write_text(payload, encoding="utf-8")

    def quote_count(self, name: str) -> int:
        return len(self.get_quotes(name))

    def _list_path(self, name: str) -> Path:
        return self._lists_dir / f"{name}.txt"

    def _validate_list_name(self, value: str) -> str:
        clean = value.strip()
        if not LIST_NAME_PATTERN.fullmatch(clean):
            raise ValueError("List name must match [A-Za-z0-9_-] and be 1-64 chars.")
        return clean


class StateRepository:
    def __init__(self, state_file: Path) -> None:
        self._state_file = state_file
        self._lock = Lock()

    def ensure_initialized(self, default_interval: int, default_list: str) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        if self._state_file.exists():
            return
        self.save(
            {
                "mode": "auto",
                "interval_seconds": default_interval,
                "active_list": default_list,
                "static_text": None,
                "static_quote": None,
                "static_until": None,
                "last_applied_text": None,
                "last_applied_at": None,
                "updated_at": utc_now_iso(),
            }
        )

    def load(self) -> dict:
        with self._lock:
            return json.loads(self._state_file.read_text(encoding="utf-8"))

    def save(self, state: dict) -> None:
        with self._lock:
            state["updated_at"] = utc_now_iso()
            temp_file = self._state_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            temp_file.replace(self._state_file)
