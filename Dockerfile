FROM python:3.9-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=never

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --all-extras --dev --no-install-project

WORKDIR /app

COPY . .

RUN uv sync --locked --all-extras --dev

CMD uv run pytest -v src/tests/integration_tests.py
