.PHONY: install format lint test

install:
	uv sync --locked
	uvx prek install

format:
	uv run ruff check --fix
	uv run ruff format

lint:
	uv run --frozen ruff check
	uv run --frozen ty check

test:
	@if [ -n "$$(find tests -name 'test_*.py' -print -quit 2>/dev/null)" ]; then \
		uv run --frozen pytest; \
	else \
		echo "No tests found; skipping tests."; \
	fi
