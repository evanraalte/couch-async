.PHONY: test lint type check

test:
	uv run pytest -vvv

lint:
	uv run ruff check --fix

type:
	uv run ty check

check:  lint type test
