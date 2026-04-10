FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project

COPY app /app/app
COPY frontend /app/frontend
COPY main.py /app/main.py

ENV TOKEN=dummy
ENV INTERVAL=3600
ENV PORT=8000
ENV DATA_DIR=/app/data
ENV LISTS_DIR=/app/data/lists
ENV STATE_FILE=/app/data/state.json

VOLUME ["/app/data"]
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "python", "-u", "main.py"]
