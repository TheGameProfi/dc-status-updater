import random
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.config import Settings, load_settings
from app.discord_client import DiscordClient
from app.engine import RuntimeEngine
from app.schemas import (
    AddQuoteRequest,
    CreateListRequest,
    RuntimeUpdateRequest,
    StaticCustomRequest,
    StaticListRequest,
)
from app.storage import QuoteRepository, StateRepository, utc_now_iso


def _select_default_list(repository: QuoteRepository) -> str:
    lists = repository.list_names()
    if not lists:
        raise RuntimeError("No quote list file exists.")
    return lists[0]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = load_settings()
    quote_repository = QuoteRepository(settings.lists_dir)
    quote_repository.ensure_initialized()

    default_list = _select_default_list(quote_repository)
    state_repository = StateRepository(settings.state_file)
    state_repository.ensure_initialized(settings.default_interval, default_list)

    client = DiscordClient(settings.token)
    engine = RuntimeEngine(quote_repository, state_repository, client)
    engine.start()

    app.state.settings = settings
    app.state.quote_repository = quote_repository
    app.state.state_repository = state_repository
    app.state.engine = engine

    yield
    engine.stop()


app = FastAPI(title="dc-status-updater", lifespan=lifespan)


def quote_repo() -> QuoteRepository:
    return app.state.quote_repository


def state_repo() -> StateRepository:
    return app.state.state_repository


def _safe_load_state() -> dict:
    state = state_repo().load()
    available_lists = quote_repo().list_names()
    if not available_lists:
        raise HTTPException(status_code=500, detail="No quote list files found.")
    if state["active_list"] not in available_lists:
        state["active_list"] = available_lists[0]
        state_repo().save(state)
    return state


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/lists")
def list_lists() -> dict:
    names = quote_repo().list_names()
    return {
        "lists": [{"name": name, "count": quote_repo().quote_count(name)} for name in names],
    }


@app.post("/api/lists")
def create_list(request: CreateListRequest) -> dict:
    try:
        quote_repo().create_list(request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.delete("/api/lists/{list_name}")
def delete_list(list_name: str) -> dict:
    names = quote_repo().list_names()
    if len(names) <= 1:
        raise HTTPException(status_code=400, detail="At least one list must remain.")

    state = _safe_load_state()
    if list_name == state["active_list"]:
        raise HTTPException(status_code=400, detail="Cannot delete active list.")

    try:
        quote_repo().delete_list(list_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@app.get("/api/lists/{list_name}/quotes")
def list_quotes(list_name: str) -> dict:
    try:
        quotes = quote_repo().get_quotes(list_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"quotes": [{"index": index, "text": text} for index, text in enumerate(quotes)]}


@app.post("/api/lists/{list_name}/quotes")
def add_quote(list_name: str, request: AddQuoteRequest) -> dict:
    try:
        quote_repo().add_quote(list_name, request.text)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.delete("/api/lists/{list_name}/quotes/{quote_index}")
def remove_quote(list_name: str, quote_index: int) -> dict:
    try:
        quote_repo().remove_quote(list_name, quote_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IndexError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.get("/api/runtime")
def get_runtime() -> dict:
    return _safe_load_state()


@app.put("/api/runtime")
def update_runtime(request: RuntimeUpdateRequest) -> dict:
    state = _safe_load_state()
    if request.mode is not None:
        state["mode"] = request.mode
        if request.mode == "auto":
            state["static_text"] = None
            state["static_quote"] = None
            state["static_until"] = None
    if request.interval_seconds is not None:
        state["interval_seconds"] = request.interval_seconds
    if request.active_list is not None:
        if request.active_list not in quote_repo().list_names():
            raise HTTPException(status_code=404, detail="List does not exist.")
        state["active_list"] = request.active_list

    state_repo().save(state)
    return state


@app.post("/api/runtime/auto")
def set_auto() -> dict:
    state = _safe_load_state()
    state["mode"] = "auto"
    state["static_text"] = None
    state["static_quote"] = None
    state["static_until"] = None
    state_repo().save(state)
    return state


@app.post("/api/runtime/pause")
def set_paused() -> dict:
    state = _safe_load_state()
    state["mode"] = "paused"
    state_repo().save(state)
    return state


@app.post("/api/runtime/static/custom")
def set_static_custom(request: StaticCustomRequest) -> dict:
    state = _safe_load_state()
    state["mode"] = "static_custom"
    state["static_text"] = request.text.strip()
    state["static_quote"] = None
    if request.duration_seconds is not None:
        state["static_until"] = (datetime.now(UTC) + timedelta(seconds=request.duration_seconds)).isoformat()
    else:
        state["static_until"] = None
    state_repo().save(state)
    return state


@app.post("/api/runtime/static/list")
def set_static_list(request: StaticListRequest) -> dict:
    state = _safe_load_state()
    list_name = request.list_name or state["active_list"]
    try:
        quotes = quote_repo().get_quotes(list_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not quotes:
        raise HTTPException(status_code=400, detail="Selected list has no quotes.")

    if request.quote_index is not None:
        if request.quote_index >= len(quotes):
            raise HTTPException(status_code=400, detail="Quote index out of range.")
        quote = quotes[request.quote_index]
    else:
        quote = random.choice(quotes)

    state["mode"] = "static_list"
    state["active_list"] = list_name
    state["static_quote"] = quote
    state["static_text"] = None
    if request.duration_seconds is not None:
        state["static_until"] = (datetime.now(UTC) + timedelta(seconds=request.duration_seconds)).isoformat()
    else:
        state["static_until"] = None
    state_repo().save(state)
    return state


@app.get("/api/now")
def now() -> dict:
    return {"now": utc_now_iso()}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
