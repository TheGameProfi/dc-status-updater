# dc-status-updater

Web UI + API for managing Discord custom status quotes with file-mounted quote lists.

## What changed

- Full refactor from a single loop script to a FastAPI service with browser UI
- Runtime modes:
  - Auto-rotate random quotes
  - Pause
  - Static custom text (with optional duration)
  - Static quote from list (with optional duration)
- Multi-file list storage:
  - One list per file in `/app/data/lists/*.txt`
  - One quote per line
- Dockerized app with optional Docker Compose setup

## Configuration

Environment variables:

- `TOKEN` (required): Discord user token
- `INTERVAL` (default: `3600`): auto mode interval in seconds
- `PORT` (default: `8000`): web server port inside container
- `DATA_DIR` (default: `/app/data`)
- `LISTS_DIR` (default: `/app/data/lists`)
- `STATE_FILE` (default: `/app/data/state.json`)

## Data layout

- Lists directory: `/app/data/lists`
  - Examples: `default.txt`, `work.txt`, `gaming.txt`
- State file: `/app/data/state.json`

## Run with Docker

```bash
docker build -t dc-status-updater .
docker run -d \
  --name dc-status-updater \
  -e TOKEN="your_discord_user_token" \
  -e INTERVAL=3600 \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  dc-status-updater
```

Open `http://localhost:8000`.

## Run with Docker Compose

1. Create `.env`:

```bash
TOKEN=your_discord_user_token
INTERVAL=3600
```

2. Start:

```bash
docker compose up -d --build
```

Open `http://localhost:8000`.

## Local run (without Docker)

```bash
python3 -m pip install --user uv
uv sync --frozen --no-dev --no-install-project
TOKEN=your_discord_user_token INTERVAL=3600 uv run --no-sync python3 main.py
```

## API overview

- `GET /api/lists`
- `POST /api/lists`
- `DELETE /api/lists/{list_name}`
- `GET /api/lists/{list_name}/quotes`
- `POST /api/lists/{list_name}/quotes`
- `DELETE /api/lists/{list_name}/quotes/{quote_index}`
- `GET /api/runtime`
- `PUT /api/runtime`
- `POST /api/runtime/auto`
- `POST /api/runtime/pause`
- `POST /api/runtime/static/custom`
- `POST /api/runtime/static/list`

## Warning

This project uses a Discord user token and may violate Discord Terms of Service. Use at your own risk.
