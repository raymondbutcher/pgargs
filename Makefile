.PHONY: all
all:
	uv sync --all-extras --dev
	uv run ruff format
	uv run ruff check --fix
	uv run mypy .
	uv run pytest -vv

int:
	docker compose build
	docker compose up --force-recreate --exit-code-from tests
	@echo integration tests successful
