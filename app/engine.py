import random
from datetime import UTC, datetime, timedelta
from threading import Event, Thread

import requests

from app.discord_client import DiscordClient
from app.storage import QuoteRepository, StateRepository, parse_iso, utc_now_iso


class RuntimeEngine:
    def __init__(
        self,
        quote_repository: QuoteRepository,
        state_repository: StateRepository,
        discord_client: DiscordClient,
    ) -> None:
        self._quote_repository = quote_repository
        self._state_repository = state_repository
        self._discord_client = discord_client
        self._stop_event = Event()
        self._thread = Thread(target=self._run_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self._stop_event.wait(timeout=1):
            try:
                self._tick()
            except (RuntimeError, PermissionError, requests.RequestException, ValueError, FileNotFoundError) as exc:
                print(f"[engine] {exc}")

    def _tick(self) -> None:
        state = self._state_repository.load()
        now = datetime.now(UTC)

        if self._maybe_expire_static(state, now):
            self._state_repository.save(state)

        mode = state["mode"]
        if mode == "paused":
            return

        desired = self._resolve_desired_status(state, now)
        if desired is None:
            return

        self._discord_client.update_status(desired)
        state["last_applied_text"] = desired
        state["last_applied_at"] = utc_now_iso()
        self._state_repository.save(state)

    def _maybe_expire_static(self, state: dict, now: datetime) -> bool:
        if state["mode"] not in {"static_custom", "static_list"}:
            return False
        until = parse_iso(state.get("static_until"))
        if until is None or now < until:
            return False

        state["mode"] = "auto"
        state["static_until"] = None
        state["static_text"] = None
        state["static_quote"] = None
        return True

    def _resolve_desired_status(self, state: dict, now: datetime) -> str | None:
        mode = state["mode"]
        if mode == "static_custom":
            text = (state.get("static_text") or "").strip()
            return text or None
        if mode == "static_list":
            text = (state.get("static_quote") or "").strip()
            return text or None

        last_applied_at = parse_iso(state.get("last_applied_at"))
        interval = int(state["interval_seconds"])
        if last_applied_at is not None and now < last_applied_at + timedelta(seconds=interval):
            return None

        quotes = self._quote_repository.get_quotes(state["active_list"])
        if not quotes:
            return None
        return random.choice(quotes)
