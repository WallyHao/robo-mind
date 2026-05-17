# RoboMind — 项目文件结构

> 整理日期：2026-05-17

---

## 设计原则

1. **源码与依赖严格分离** — 可 git clone / pip install 的一律不进 repo
2. **模块化** — brain.py 的 600+ 行单体拆分为独立模块
3. **无硬编码** — 路径、API Key 全部走环境变量或配置文件
4. **命令行交互** — 废弃原 Gradio Web UI，改为终端交互式 REPL，输出纯 ASCII 无 emoji
5. **一键启动** — `make run` 同时拉起 body + brain 进程
6. **类型安全** — 所有公共函数带类型标注，CI 中 mypy 严格模式检查
7. **结构化日志** — 用 `logging` 替代 `print()`，支持级别过滤和文件输出
8. **配置校验** — 启动时用 pydantic 校验所有配置，非法参数立即报错而非静默失败
9. **可复现环境** — `pyproject.toml` 锁定依赖版本 + Dockerfile 统一运行环境

---

## 文件结构

```
RoboMind/
│
├── AGENTS.md                         # 本文件（项目结构说明）
├── README.md                         # 快速入门指南
├── pyproject.toml                    # 项目元数据 + 依赖声明 + 工具配置
├── Makefile                          # 常用命令入口（lint/test/install/run）
├── CHANGELOG.md                      # 版本变更记录
├── .gitignore                        # 忽略规则
├── .env.example                      # 环境变量模板（不含真实 Key）
├── .pre-commit-config.yaml           # pre-commit hooks（ruff/mypy）
├── Dockerfile                        # 可复现的容器化运行环境
├── run.py                            # ★ 一键启动：同时拉起 body + brain 进程（rich 彩色输出）
│
├── src/                              # ★ 核心项目源码
│   └── robomind/
│       ├── __init__.py
│       │
│       ├── body.py                   # 物理身体进程
│       │                             #   加载 OmniGibson 场景 + Fetch 机器人
│       │                             #   订阅 /cmd_vel，发布 /odom、/camera_rgb
│       │
│       ├── brain.py                  # 大脑进程入口
│       │                             #   命令行 REPL：接收用户输入 → 执行 → 打印结果
│       │
│       ├── skills/                   # 技能模块
│       │   ├── __init__.py
│       │   ├── base.py               #   Skill 抽象基类
│       │   ├── registry.py           #   SkillRegistry 调度中心
│       │   ├── navigation.py         #   navigate / stop / turn
│       │   ├── perception.py         #   look / navigate_to_object
│       │   └── positioning.py        #   get_position
│       │
│       ├── llm/                      # LLM / VLM 交互层
│       │   ├── __init__.py
│       │   ├── planner.py            #   自然语言 → JSON 任务序列
│       │   ├── vl_model.py           #   VLM 视觉识别封装
│       │   └── errors.py             #   LLM/VLM 专用异常类型
│       │
│       ├── comm/                     # 通信层
│       │   ├── __init__.py
│       │   ├── lcm_bridge.py         #   LCM 收发 / 解码 / 编码 / 线程管理
│       │   └── types.py              #   消息类型别名（Twist, Odometry, Image）
│       │
│       └── config/                   # 配置加载与校验
│           ├── __init__.py
│           ├── body_config.py        #   BodyConfig (pydantic model)
│           ├── brain_config.py       #   BrainConfig (pydantic model)
│           └── loader.py             #   YAML → pydantic 加载器
│
├── tests/                            # 测试
│   ├── __init__.py
│   ├── conftest.py                   #   pytest fixtures（mock LCM、mock LLM）
│   ├── test_skills/
│   │   ├── test_navigation.py
│   │   ├── test_perception.py
│   │   └── test_positioning.py
│   ├── test_llm/
│   │   ├── test_planner.py
│   │   └── test_vl_model.py
│   └── test_comm/
│       └── test_lcm_bridge.py
│
├── training/                         # Pi05 模型训练工具（独立子项目）
│   ├── README.md                     #   训练流程说明
│   └── download_model.py             #   从 HuggingFace 下载 Pi05 预训练权重
│
├── scripts/                          # 辅助脚本
│   └── install_deps.sh               #   一键安装外部依赖（dimOS/BEHAVIOR）
│
├── configs/                          # YAML 配置文件
│   ├── body.yaml                     #   OmniGibson 场景/机器人配置
│   ├── brain.yaml                    #   LLM/VLM 模型选择、LCM 参数
│   └── prompts/                      #   LLM 提示词模板
│       └── task_planner.txt          #   任务规划系统提示词
│
├── deps/                             # 外部依赖清单（不含依赖本身）
│   └── README.md                     #   所有外部依赖的安装指南
│
└── logs/                             # 运行时日志输出（.gitignore 忽略内容）
    └── .gitkeep
```

---

## 启动方式

```bash
python run.py
# 或通过 Makefile
make run
```

`run.py` 负责：
1. 加载 `.env` 和 `configs/*.yaml`，pydantic 校验配置合法性
2. 在后台启动 body.py 子进程，通过 LCM 监听等待 `/odom` 首次到达，确认仿真就绪
3. 在前台启动 brain.py 子进程，进入交互 REPL

终端输出使用 `rich` 库实现彩色渲染：
- `[dim]` 灰色 — 时间戳和模块名前缀
- `[cyan]` 青色 — 信息性输出 ([INFO])
- `[yellow]` 黄色 — 警告 ([WARN])
- `[red]` 红色 — 错误 ([ERROR])
- `[green]` 绿色 — 成功 ([OK])
- `[magenta]` 紫色 — LLM 交互 ([LLM])
- `[blue]` 蓝色 — 执行进度 ([EXEC])
- `[bright_white]` 亮白 — 完成标记 ([DONE])

退出一律用 `Ctrl+C`，`run.py` 捕获 `SIGINT` 后依次 `terminate()` 两个子进程。

---

## 命令行交互流程

命令行输出全部使用纯 ASCII，不包含 emoji 或其他 Unicode 装饰字符。

```
$ ./run.sh
[INFO] body: scene Rs_int loaded, Fetch robot ready
[INFO] brain: 6 skills registered, waiting for input

RoboMind> go to the door
[LLM] parsed 2 tasks:
  [1] navigate_to_object -- approach the door using visual feedback
  [2] stop -- halt

[EXEC] task 1/2: navigate_to_object
  desc: approach the door using visual feedback
  [1] size=0.12 offset=+0.23
  [2] size=0.18 offset=+0.08
  [3] size=0.31 offset=+0.02
  [OK] arrived near 'door'

[EXEC] task 2/2: stop
  [OK] halted

[DONE] all tasks completed

RoboMind> look chair
[EXEC] task 1/1: look
  [OK] found 'chair': bbox=[320,180,480,400]
  offset: +0.08 (right)

RoboMind> exit
[INFO] shutting down...
```

支持的 REPL 命令：
- 任意自然语言 → LLM 拆解 → 执行
- `/skills` → 列出所有可用技能
- `/dry <指令>` → 仅预览 LLM 拆解结果，不执行
- `/pos` → 查询当前位置
- `/help` → 打印帮助
- `exit` / `quit` → 退出

日志输出规范：
- `[INFO]` 常规状态（启动、就绪、完成）
- `[WARN]` 可恢复异常（解码失败、重试）
- `[ERROR]` 不可恢复错误（连接断开、配置无效）
- `[EXEC]` 任务执行进度
- `[LLM]` 大模型交互
- `[OK]` 操作成功结果

---

## 不放入本目录的内容（外部依赖）

以下全部通过 `deps/install_deps.sh` 或手动安装获取，**不**拷贝到 RoboMind：

| 依赖 | 获取方式 | 用途 |
|------|----------|------|
| **dimOS** | `git clone https://github.com/dimensionalOS/dimos.git` | LCM 消息定义、导航/感知算法 |
| **OmniGibson** | `git clone` (BEHAVIOR-1K 子模块) | Isaac Sim 物理仿真引擎 |
| **BEHAVIOR-1K** | `git clone https://github.com/StanfordVL/BEHAVIOR-1K.git` | 场景、任务、3D 资产 |
| **LeRobot** | `pip install lerobot` 或 `git clone` | Pi05 训练框架 |
| **Pi05 模型** | `huggingface_hub.snapshot_download("lerobot/pi05_base")` | VLA 预训练权重 |
| **Conda/venv** | 按文档重建 | Python 运行环境 |

---

## 模块依赖关系

```
run.py ──┬── body.py ──── comm/lcm_bridge.py ──── LCM ──┐
         │                                               │
         └── brain.py ─── comm/lcm_bridge.py ──── LCM ──┘
              │
              ├── llm/planner.py         (LLM 任务拆解)
              ├── llm/vl_model.py        (VLM 视觉识别)
              ├── skills/registry.py ────┐
              │   ├── navigation.py      │
              │   ├── perception.py ─────┤ (调用 vl_model.py)
              │   └── positioning.py     │
              └── (内置 REPL 循环)       │
                                         │
              ═════ LCM UDP Multicast ════
```

---

## 配置管理约定

- **敏感信息**（API Key）→ 环境变量（复制 `.env.example` 为 `.env` 后填写）
- **项目路径**（dimOS、BEHAVIOR-1K 安装位置等）→ `configs/brain.yaml`
- **仿真参数**（场景、机器人、相机）→ `configs/body.yaml`
- **LLM 提示词**→ `configs/prompts/` 目录下独立 `.txt` 文件

---

## 工程质量规范

### 1. pyproject.toml — 统一项目元数据

替代散落的 `requirements.txt`、`setup.py`，在一个文件中声明：

```toml
[project]
name = "robomind"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.24",
    "lcm",
    "openai>=1.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock",
    "ruff>=0.5",
    "mypy>=1.10",
    "pre-commit>=3.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
strict = true
```

新成员只需 `pip install -e ".[dev]"` 即获得完整开发环境。

### 2. Makefile — 消除"记不住命令"问题

```makefile
.PHONY: install lint typecheck test run clean

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

test:
	pytest -v --cov=robomind --cov-report=term-missing

run:
	python run.py

clean:
	rm -rf logs/*.log
```

### 3. 类型标注 — mypy strict 模式

原始代码中大量隐式 `Any`，重构后要求：

```python
# BAD: 无类型标注，隐式 Any
def _publish_twist(linear_x, angular_z):
    msg = _Twist(linear=[linear_x, 0.0, 0.0], ...)

# GOOD: 完整类型标注，mypy strict 可通过
def publish_twist(linear_x: float, angular_z: float) -> None:
    msg = Twist(linear=[linear_x, 0.0, 0.0], angular=[0.0, 0.0, angular_z])
    self._lc.publish("/cmd_vel", msg.lcm_encode())
```

### 4. 结构化日志 — 替代 print()

```python
# BAD: 输出不可控，无时间戳，无级别，带 unicode 装饰
print(f"[Body] /cmd_vel decode failed: {e}")

# GOOD: 可配级别、可输出到文件、自带时间戳和模块名
import logging
logger = logging.getLogger(__name__)

logger.warning("/cmd_vel decode failed", exc_info=True)
logger.info("odom published | x=%.2f y=%.2f", pos[0], pos[1])
```

启动时自动将日志同时输出到终端和 `logs/body_{date}.log`。

### 5. pydantic 配置校验 — 启动时拦截错误配置

```python
from pydantic import BaseModel, Field

class BodyConfig(BaseModel):
    scene_model: str = Field(default="Rs_int", pattern=r"^[A-Z][a-z]+_[a-z]+$")
    robot_type: str = Field(default="Fetch")
    canvas_width: int = Field(default=640, ge=320, le=1920)
    canvas_height: int = Field(default=480, ge=240, le=1080)
    odom_hz: int = Field(default=20, ge=1, le=60)
    camera_hz: int = Field(default=6, ge=1, le=30)

class BrainConfig(BaseModel):
    llm_backend: str = Field(default="deepseek", pattern=r"^(deepseek)$")
    vlm_backend: str = Field(default="qwen", pattern=r"^(qwen|deepseek|openai)$")
    lcm_channel_cmd_vel: str = "/cmd_vel"
    lcm_channel_odom: str = "/odom"
    lcm_channel_camera: str = "/camera_rgb"
```

非法 YAML 会在启动第一秒报错，而非跑到一半崩溃。

### 6. pre-commit — 提交前自动检查

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-pyyaml]
```

新成员克隆后执行 `pre-commit install`，每次 `git commit` 自动跑 lint + typecheck。

### 7. Dockerfile — 消灭"我这能跑你那不行"

```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3.10 python3-pip
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
CMD ["python", "run.py"]
```

配合 NVIDIA Container Toolkit，任何有 GPU 的机器 `docker compose up` 即跑。

### 8. 单元测试 — 用 mock 隔离外部依赖

原项目无法测试因为强绑定 Isaac Sim / LCM / DeepSeek API。重构后：

```python
# tests/test_llm/test_planner.py
def test_planner_parses_valid_json(mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = fake_response(
        '[{"skill": "stop", "params": {}, "description": "停住"}]'
    )
    tasks = TaskPlanner().parse("stop")
    assert len(tasks) == 1
    assert tasks[0].skill == "stop"

def test_planner_handles_markdown_wrapper(mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = fake_response(
        '```json\n[{"skill": "stop", "params": {}, "description": "停住"}]\n```'
    )
    tasks = TaskPlanner().parse("stop")
    assert tasks[0].skill == "stop"
```

### 9. 自定义异常 — 让错误信息有意义

```python
# src/robomind/llm/errors.py
class LLMError(Exception): ...
class LLMParseError(LLMError): ...       # JSON 解析失败
class LLMTimeoutError(LLMError): ...     # API 超时
class VLMNotConfiguredError(Exception): ...  # 未配置视觉模型
class LCMConnectionError(Exception): ...     # LCM 通信失败
```

替代原始代码中 `pass` 吞掉异常的写法（如原 `only_body.py:54`）。

### 10. 依赖锁定 — 确保持久可复现

```bash
pip-compile pyproject.toml -o requirements-lock.txt   # pip-tools
# 或
conda env export --no-builds > environment-lock.yml    # conda
```

锁定文件提交到仓库，保证半年后仍可精确复现相同环境。

### 11. run.py — Python 启动器 + rich 彩色终端

```python
# run.py
import subprocess
import signal
import sys
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table

console = Console()
processes: list[subprocess.Popen] = []

def cleanup(signum: int, frame: object) -> None:
    console.print("\n[yellow]shutting down...[/yellow]")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

console.print(Panel.fit(
    "[bold cyan]RoboMind[/bold cyan] v0.1.0",
    subtitle="body + brain dual-process architecture",
))
console.print("[dim]starting body process...[/dim]")
# ... spawn body.py, wait for /odom, spawn brain.py ...
```

子进程输出通过 `rich` 自动换色转发，`run.py` 本身不参与 LCM 通信，只做进程管理和终端渲染。


## 原始项目问题 → 解决方案对照

| 原始问题 | 后果 | RoboMind 解决方案 |
|----------|------|-------------------|
| 路径硬编码 | 换个用户名就跑不了 | 配置文件 + 环境变量 + pydantic 校验 |
| API Key 明文写在代码里 | 安全风险 + git 泄漏 | `.env` 文件 + `.gitignore` |
| `print()` 到处乱打 | 无级别过滤，无时间戳 | `logging` + 文件输出 |
| `except Exception: pass` | 静默失败，查 bug 靠猜 | 自定义异常 + `exc_info=True` |
| 600 行单体 brain.py | 修改一处不敢动别处 | 拆分为 10+ 个小模块 |
| 无测试 | 改一行不知道坏没坏 | pytest + CI + coverage |
| 无 mypy | 类型错误运行时才暴露 | mypy strict + pre-commit |
| 废弃文件混在根目录 | 新成员不知道哪个是入口 | 全部删除，只保留活跃代码 |
| 无 Makefile | 每个新人问一遍"怎么跑" | `make run` / `make test` |
| 三个 LeRobot 副本 | 混乱，占空间 | git clone 一次，从 deps/ 引用 |
| tar + 解压目录并存 | 重复占用 | 删 tar，gitignore 模型文件 |
| 虚拟环境不可移植 | 换机器要重建 | `pyproject.toml` + Dockerfile |


## 与原始项目的对应关系

| 原始文件 | RoboMind 位置 | 变化 |
|----------|---------------|------|
| `behavior_root/body.py` | `src/robomind/body.py` | 路径硬编码 → 配置文件 |
| `behavior_root/brain.py` | `src/robomind/brain.py` + `skills/*` + `llm/*` + `comm/*` | 单体拆模块，Gradio → CLI REPL |
| `behavior_root/only_body.py` | — | 废弃，已删除 |
| `behavior_root/only_brain.py` | — | 废弃，已删除 |
| `behavior_root/dimos_bridge.py` | — | 废弃，已删除 |
| `pi05_workdir/lerobot/download_model.py` | `training/download_model.py` | 硬编码路径 → 命令行参数 |
