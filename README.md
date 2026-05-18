# RoboMind

Embodied robot control with a dual-process body/brain architecture over LCM.

```

RoboMind/
├── src/robomind/       Core source code
│   ├── body.py         Physics simulation process
│   ├── brain.py        LLM task planning + CLI REPL
│   ├── skills/         Skill implementations
│   ├── llm/            LLM/VLM integration
│   ├── comm/           LCM communication layer
│   └── config/         pydantic config models
├── configs/            YAML configuration files
├── tests/              pytest test suite
├── training/           Pi05 model training utilities
├── run.py              Colored terminal launcher
└── scripts/            Utility scripts
```

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| NVIDIA GPU + CUDA 12.x | Required for Isaac Sim / OmniGibson |
| Isaac Sim | Requires [NVIDIA Omniverse](https://www.nvidia.com/en-us/omniverse/) license |
| Python 3.10+ | Recommend conda or venv |

## Setup

### 1. Clone and create environment

```bash
git clone <repo-url> RoboMind
cd RoboMind

conda create -n robomind python=3.10 -y
conda activate robomind

pip install -e ".[dev]"
```

> ```bash
> pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 2. Install external dependencies

The project depends on three large external projects that are **not** included in this repo.

**dimOS** — LCM messaging, navigation and perception

```bash
git clone https://github.com/dimensionalOS/dimos.git
cd dimos
pip install -e .
cd ..
```

**BEHAVIOR-1K + OmniGibson** — Simulation environment

```bash
git clone https://github.com/StanfordVL/BEHAVIOR-1K.git
cd BEHAVIOR-1K
git submodule update --init --recursive
pip install -e OmniGibson/
cd ..
```

**Pi05 Model** (training only, optional)

```bash
export HF_ENDPOINT=https://hf-mirror.com

pip install huggingface_hub
python training/download_model.py
```

### 3. Configure

Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx          # DeepSeek API key (LLM)
ALIBABA_API_KEY=sk-xxxxxxxx           # Alibaba Bailian API key (VLM)
DIMOS_SITE_PATH=/path/to/dimos/site-packages
BEHAVIOR_DIR=/path/to/BEHAVIOR-1K
```

### 4. Run

```bash
make run
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install project + dev dependencies |
| `make lint` | Run ruff linter |
| `make typecheck` | Run mypy strict type checking |
| `make test` | Run pytest with coverage |
| `make run` | Launch body + brain processes |
| `make clean` | Remove caches and logs |

## Skills

| Skill | Description |
|-------|-------------|
| `navigate` | Blind timed navigation |
| `stop` | Immediate halt |
| `turn` | Rotate in place |
| `get_position` | Query current coordinates |
| `look` | VLM object detection in camera |
| `navigate_to_object` | Visual closed-loop approach |

## REPL Usage

```
RoboMind> go to the door
[LLM] parsed 2 tasks:
  [1] navigate_to_object -- approach the door
  [2] stop -- halt
[OK] arrived near 'door'
[DONE] all tasks completed

RoboMind> /help      # show available commands
RoboMind> /skills    # list available skills
RoboMind> /dry <cmd> # preview task plan without executing
RoboMind> /pos       # query current position
RoboMind> exit       # quit
```
