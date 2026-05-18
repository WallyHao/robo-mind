.PHONY: install lint typecheck test run clean

SHELL := /bin/bash
CONDA_ENV_PREFIX := /media/waliwuao/WorkSpace/robomind_env
_CONDA_RUN := $(shell test -d $(CONDA_ENV_PREFIX) && echo "conda run --prefix $(CONDA_ENV_PREFIX)" || echo "")

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

test:
	@if [ -n "$(_CONDA_RUN)" ]; then \
		PYTHONPATH="" $(_CONDA_RUN) pytest; \
	else \
		PYTHONPATH="" pytest; \
	fi

ISAAC_SIM_PATH := /media/waliwuao/WorkSpace/isaac_sim

run:
	@if [ -d "$(CONDA_ENV_PREFIX)" ]; then \
		eval "$$(conda shell.bash hook)" && \
		conda activate "$(CONDA_ENV_PREFIX)" && \
		export ISAAC_PATH="$(ISAAC_SIM_PATH)" && \
		export EXP_PATH="$(ISAAC_SIM_PATH)/apps" && \
		export CARB_APP_PATH="$(ISAAC_SIM_PATH)/kit" && \
		export LD_LIBRARY_PATH="$$LD_LIBRARY_PATH:$(ISAAC_SIM_PATH)/.:$(ISAAC_SIM_PATH)/kit:$(ISAAC_SIM_PATH)/kit/kernel/plugins:$(ISAAC_SIM_PATH)/kit/libs/iray:$(ISAAC_SIM_PATH)/kit/plugins:$(ISAAC_SIM_PATH)/kit/plugins/bindings-python:$(ISAAC_SIM_PATH)/kit/plugins/carb_gfx:$(ISAAC_SIM_PATH)/kit/plugins/rtx:$(ISAAC_SIM_PATH)/kit/plugins/gpu.foundation" && \
		export PYTHONPATH="$$PYTHONPATH:$(ISAAC_SIM_PATH)/kit/kernel/py:$(ISAAC_SIM_PATH)/kit/plugins/bindings-python:$(ISAAC_SIM_PATH)/exts/isaacsim.simulation_app:$(ISAAC_SIM_PATH)/python_packages" && \
		python run.py; \
	else \
		python run.py; \
	fi

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf logs/*.log
	rm -rf .mypy_cache .ruff_cache
