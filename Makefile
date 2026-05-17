.PHONY: install lint typecheck test run clean

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

test:
	pytest

run:
	python run.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf logs/*.log
	rm -rf .mypy_cache .ruff_cache
