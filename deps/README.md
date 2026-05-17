# External Dependencies

RoboMind 依赖以下外部项目，需要预先安装。这些依赖**不**包含在本仓库中。

## Prerequisites

- NVIDIA GPU + CUDA 12.x
- NVIDIA Isaac Sim (requires separate license)
- Python 3.10+
- Conda or venv

## 1. dimOS — Robot Operating System

dimOS provides LCM message definitions, navigation algorithms, and perception modules.

```bash
git clone https://github.com/dimensionalOS/dimos.git /path/to/dimos
cd /path/to/dimos
pip install -e .
```

Set `DIMOS_SITE_PATH` in `.env` to point to the installed site-packages directory.

## 2. BEHAVIOR-1K + OmniGibson — Simulation Environment

BEHAVIOR-1K provides household scenes, 3D assets, and task definitions.
OmniGibson is the NVIDIA Isaac Sim-based physics engine.

```bash
git clone https://github.com/StanfordVL/BEHAVIOR-1K.git /path/to/BEHAVIOR-1K
cd /path/to/BEHAVIOR-1K
git submodule update --init --recursive
pip install -e OmniGibson/
```

Set `BEHAVIOR_DIR` in `.env` to point to the cloned repository.

## 3. LeRobot + Pi05 Model — Training (optional)

```bash
pip install lerobot
python -c "
from huggingface_hub import snapshot_download
snapshot_download('lerobot/pi05_base', local_dir='./pi05_model')
"
```

## 4. Python Environment

```bash
conda create -n robomind python=3.10
conda activate robomind
pip install -e ".[dev]"
```
