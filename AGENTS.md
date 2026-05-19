# RoboMind — Agent Instructions

> Last verified: 2026-05-19

## Commands

All via `make` or direct equivalents:

| Command             | What it runs                                      |
|---------------------|---------------------------------------------------|
| `make install`      | `pip install -e ".[dev]"` + `pre-commit install`  |
| `make lint`         | `ruff check src/ tests/`                          |
| `make typecheck`    | `mypy src/`                                       |
| `make test`         | `pytest` (includes `--cov=robomind`)              |
| `make run`          | `python run.py`                                   |
| `make clean`        | remove `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `logs/*.log` |

**Pre-commit** runs `ruff`, `ruff-format`, and `mypy` on every commit. CI does not exist yet — pre-commit is the only quality gate.

Run a single test file: `pytest tests/test_llm/test_planner.py`

### Makefile gotchas

- `make test` unconditionally sets `PYTHONPATH=""` before running pytest — this isolates tests from any
  external PYTHONPATH pollution (notably the dimOS/Isaac Sim injection used at runtime).
- `make run` requires `CONDA_ENV_PREFIX` and `ISAAC_SIM_PATH` in `.env`. These are
  machine-specific paths; copy `.env.example` and fill them in.
  - **Python version**: Isaac Sim's compiled `carb._carb` module requires Python **3.11**.
    A Python 3.12 conda env will fail with `No module named 'carb._carb'`.
- Dependencies can also be installed via `pip install -r requirements.txt` (same packages as
  `pyproject.toml`).

## Architecture

Two processes communicate exclusively through **LCM UDP multicast**:

- **`run.py`** — launcher; spawns body+brain subprocesses, checks for `.env`/`DIMOS_SITE_PATH`,
  prints status via `rich`. Uses `python-dotenv` to auto-load `.env` (no manual `source` needed).
- **`body.py`** — simulation process. Loads OmniGibson, subscribes `/cmd_vel`, publishes `/odom`
  and `/camera_rgb`.
- **`brain.py`** — REPL process. Subscribes `/odom` + `/camera_rgb`, publishes `/cmd_vel`. Uses
  LLM to decompose natural language into skill tasks.

Both processes share `LcmBridge` (`comm/lcm_bridge.py`) which wraps `lcm.LCM()` with a daemon
handler thread and thread-safe read/write accessors.

Message types (`comm/types.py`) re-export from **dimOS** (`dimos.msgs.*`). dimOS must be installed
externally and pointed to via `DIMOS_SITE_PATH` env var — its path is injected into `sys.path`
before imports. The same file also defines `Task` and `BBox` dataclasses and
`OpenAICompatibleVlModel`.

## Configuration

- **`.env`** — secrets (API keys), `DIMOS_SITE_PATH`, `CONDA_ENV_PREFIX`, `ISAAC_SIM_PATH`.
  Copy from `.env.example`.
- **`configs/body.yaml`** — OmniGibson scene/robot/timing/LCM settings → validated by
  `config/body_config.py` (pydantic)
- **`configs/brain.yaml`** — LLM/VLM backend selection, LCM channels, logging → validated by
  `config/brain_config.py` (pydantic)
- **`configs/prompts/task_planner.txt`** — LLM system prompt for task decomposition

All config files are validated at import time. Bad YAML fails fast.

## Module Map

```
src/robomind/
  body.py          — OmniGibson simulation loop (entry: robomind.body:main)
  brain.py         — REPL + task dispatch (entry: robomind.brain:main)
  comm/
    lcm_bridge.py  — LCM pub/sub with background thread
    types.py       — Twist, Odometry, Pose, RoboImage re-exports + Task/BBox dataclasses + OpenAICompatibleVlModel
  config/
    body_config.py — BodyConfig (pydantic, nested sub-models)
    brain_config.py— BrainConfig (pydantic)
    loader.py      — YAML loading helpers
  llm/
    planner.py     — TaskPlanner: natural language → list[Task] via DeepSeek API
    vl_model.py    — VlModelProtocol, build_vl_model(), get_object_bbox()
    errors.py      — LLMParseError, LLMTimeoutError, VLMNotConfiguredError, LCMConnectionError
  skills/
    base.py        — Skill Protocol + SkillResult dataclass
    registry.py    — SkillRegistry (dict dispatch)
    navigation.py  — NavigateSkill, StopSkill, TurnSkill
    perception.py  — LookSkill, NavigateToObjectSkill
    positioning.py — GetPositionSkill
```

## REPL Commands

```
RoboMind> <any natural language>     # LLM decomposes → executes skills
RoboMind> /skills                    # list registered skills
RoboMind> /dry <instruction>         # preview LLM decomposition, don't execute
RoboMind> /pos                       # query current robot position
RoboMind> /help                      # print help
RoboMind> exit / quit                # shutdown
```

Ctrl+C triggers graceful shutdown (both processes via `run.py`).

## Code Conventions

- **No emojis in output** — all REPL output uses plain ASCII tags: `[LLM]`, `[EXEC]`, `[OK]`,
  `[DONE]`, `[WARN]`, `[ERROR]`
- **Logging over print** — all modules use `logging.getLogger(__name__)`. Only `brain.py` REPL uses
  `print()` for user-facing output.
- **Type annotations everywhere** — `mypy --strict` enforced, with `ignore_missing_imports = true`
  for dimOS/lcm.
- **ruff config**: line-length=100, target-version=py310, double-quote style, selects
  E/F/I/N/W/UP/B/SIM
- **No hardcoded paths or keys** — all go through configs or env vars
- **Imports**: `from __future__ import annotations` in every file. dimOS imports happen after
  `sys.path` setup.
- **Proxy stripping**: both `body.py` and `brain.py` strip `http_proxy`/`https_proxy` (and
  variants) from the environment before importing any packages. This prevents OpenSSL certificate
  errors from proxy interception.

## Environment Requirements

1. `DIMOS_SITE_PATH` must be set in `.env` — points to dimOS site-packages directory
2. `DEEPSEEK_API_KEY` — required for LLM task planning
3. `ALIBABA_API_KEY` or `DASHSCOPE_API_KEY` — required for Qwen VLM (or
   `DEEPSEEK_API_KEY`/`OPENAI_API_KEY` for other VLM backends)
4. OmniGibson (Isaac Sim backend) must be installed externally — not pip-installable
5. `pip install -e ".[dev]"` installs all Python deps in the correct venv

## Testing

Tests live under `tests/` mirroring the `src/robomind/` layout:
- `tests/conftest.py` — provides `mock_openai_client` fixture (mocks `openai.OpenAI`)
- `tests/test_llm/` — TaskPlanner and VLM tests
- `tests/test_skills/` — navigation, perception, positioning
- `tests/test_comm/` — LcmBridge tests

Tests are fully offline — they mock LCM and LLM/VLM APIs. No simulation required.

## External Dependencies (not in repo)

| Dependency  | Purpose                    | Install via                          |
|-------------|----------------------------|--------------------------------------|
| dimOS       | LCM message definitions    | git clone + DIMOS_SITE_PATH env var  |
| OmniGibson  | Physics simulation         | git clone (BEHAVIOR-1K submodule)    |
| BEHAVIOR-1K | Scenes, assets             | git clone + setup script             |
| LeRobot     | Pi05 training framework    | pip install lerobot                  |
| Pi05 model  | VLA pretrained weights     | huggingface_hub.snapshot_download    |

See `deps/README.md` and `scripts/install_deps.sh` for setup details.
