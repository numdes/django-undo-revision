.PHONY: all fmt lint lock typecheck test check

fmt:
	uv run ruff format undo_revision

lint:
	uv run ruff check undo_revision

lock:
	uv lock --check

typecheck:
	uv run mypy undo_revision tests

test:
	uv run pytest tests/

all: fmt lint lock typecheck test

check: all
