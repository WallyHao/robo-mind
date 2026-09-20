# Contributing

Thanks for your interest in RoboMind. The project is a research prototype, so
changes that keep the body/brain boundary explicit and the offline tests green
are welcome.

## Development Setup

```bash
git clone https://github.com/WallyHao/robomind.git
cd robomind
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

The simulation stack (OmniGibson / BEHAVIOR-1K / Isaac Sim) and dimOS are
installed separately and are **not** required to run the tests. dimOS supplies
the LCM message types; without it the package still imports and the pure
dataclasses remain usable.

## Before Opening A Pull Request

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

CI runs the same checks on Python 3.10 to 3.13.

## Guidelines

- Keep the body process and the brain process decoupled; they must only talk
  through `LcmBridge` channels.
- Add or update tests for every behavior change. The configuration, planner,
  skill registry and LCM bridge are testable without a simulator.
- Type annotations are enforced with `mypy --strict`; do not widen types to
  silence the checker.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
