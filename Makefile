.PHONY: all
all:
	uv sync --all-extras --dev
	uv run ruff format
	uv run ruff check --fix
	uv run mypy .
	uv run pytest -vv
