# Changelog

## [0.1.1] — 2026-05-18

### Added
- Auto-load `.env` via `python-dotenv` in `run.py`, no longer requires manual `export`
- `python-dotenv>=1.0` added to core dependencies in `pyproject.toml`

### Fixed
- `DIMOS_SITE_PATH` corrected in `.env.example` to match editable dimOS install path
- Makefile `run` target now sources Isaac Sim environment (`ISAAC_PATH`, `EXP_PATH`, `CARB_APP_PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH`) to avoid `SRE module mismatch` / `No module named 'carb._carb'` errors
- Makefile `test` target now runs via conda environment when available
- Makefile sets `SHELL := /bin/bash` to ensure script compatibility

## [0.1.0] — 2026-05-17

- Initial project structure extracted from original monorepo
- Dual-process body/brain architecture via LCM
- 6 skills: navigate, stop, turn, look, get_position, navigate_to_object
- LLM task planning (DeepSeek) + VLM visual perception (Qwen/DeepSeek/OpenAI)
- CLI REPL interface replacing Gradio Web UI
- pydantic-based configuration validation
- pytest test suite with mocked external dependencies
- rich-powered colored terminal output
