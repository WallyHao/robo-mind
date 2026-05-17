from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from pathlib import Path

from robomind.comm.lcm_bridge import LcmBridge
from robomind.comm.types import Task
from robomind.config.brain_config import BrainConfig
from robomind.config.loader import load_brain_config, load_task_planner_prompt
from robomind.llm.errors import LLMParseError
from robomind.llm.planner import TaskPlanner
from robomind.llm.vl_model import VlModelProtocol, build_vl_model
from robomind.skills.navigation import NavigateSkill, StopSkill, TurnSkill
from robomind.skills.perception import LookSkill, NavigateToObjectSkill
from robomind.skills.positioning import GetPositionSkill
from robomind.skills.registry import SkillRegistry

logger = logging.getLogger("robomind.brain")


def _strip_markdown_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _setup_imports() -> None:
    for key in (
        "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
        "all_proxy", "ALL_PROXY", "socks_proxy", "SOCKS_PROXY",
    ):
        os.environ.pop(key, None)

    dimos_lib = os.environ.get("DIMOS_SITE_PATH", "")
    if not dimos_lib:
        raise RuntimeError(
            "DIMOS_SITE_PATH not set. Please set it in .env file "
            "to point to the installed dimOS package location."
        )
    if dimos_lib not in sys.path:
        sys.path.insert(0, dimos_lib)


def _setup_logging(config: BrainConfig) -> None:
    os.makedirs("logs", exist_ok=True)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if config.logging.file:
        handlers.append(logging.FileHandler(config.logging.file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


_repl_help = """Commands:
  <natural language>   execute task via LLM decomposition
  /skills              list available skills
  /dry <instruction>   preview LLM task decomposition (no execution)
  /pos                 query current robot position
  /help                show this help
  exit, quit           shutdown"""


def main() -> None:
    _setup_imports()

    config = load_brain_config()
    _setup_logging(config)

    lcm = LcmBridge(body_mode=False)
    lcm.sub_odom()
    lcm.sub_camera()
    lcm.start()

    planner = TaskPlanner(
        system_prompt=load_task_planner_prompt(),
        backend=config.llm.backend,
        temperature=config.llm.temperature,
    )

    vl_model: VlModelProtocol | None = None
    try:
        vl_model = build_vl_model(backend=config.vlm.backend)
        logger.info("VLM backend '%s' initialized", config.vlm.backend)
    except Exception:
        logger.warning("VLM not configured, look/navigate_to_object will be unavailable")

    registry = SkillRegistry()
    registry.register(NavigateSkill(lcm))
    registry.register(StopSkill(lcm))
    registry.register(TurnSkill(lcm))
    registry.register(GetPositionSkill(lcm))
    if vl_model is not None:
        registry.register(LookSkill(lcm, vl_model))
        registry.register(NavigateToObjectSkill(lcm, vl_model))

    logger.info("brain ready | %d skills registered", len(registry))

    print(f"RoboMind v0.1.0 — {len(registry)} skills loaded. Type /help for commands.\n")

    try:
        _repl(registry, planner, config)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        logger.info("shutting down brain process")
        lcm.stop()


def _repl(registry: SkillRegistry, planner: TaskPlanner, config: BrainConfig) -> None:
    while True:
        try:
            raw = input("RoboMind> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        if raw in ("exit", "quit"):
            break

        if raw == "/help":
            print(_repl_help)
            continue

        if raw == "/skills":
            print("available skills:", ", ".join(registry.list_skills()))
            continue

        if raw == "/pos":
            print(registry.run("get_position"))
            continue

        if raw.startswith("/dry "):
            command = raw[5:].strip()
            _dry_run(planner, command)
            continue

        if raw.startswith("/"):
            print(f"unknown command: {raw}, type /help")
            continue

        _execute(registry, planner, raw, config)


def _dry_run(planner: TaskPlanner, command: str) -> None:
    print("task preview (dry-run):")
    try:
        tasks = planner.parse(command)
        for i, t in enumerate(tasks, 1):
            print(f"  [{i}] {t.skill}: {json.dumps(t.params, ensure_ascii=False)}  # {t.description}")
        print()
    except LLMParseError as e:
        print(f"LLM response could not be parsed: {e}")
    except Exception:
        print(f"LLM call failed:\n{traceback.format_exc()}")


def _execute(
    registry: SkillRegistry,
    planner: TaskPlanner,
    command: str,
    config: BrainConfig,
) -> None:
    try:
        tasks = planner.parse(command)
    except LLMParseError as e:
        print(f"LLM response could not be parsed: {e}")
        return
    except Exception:
        print(f"LLM call failed:\n{traceback.format_exc()}")
        return

    print(f"[LLM] parsed {len(tasks)} tasks:")
    for i, t in enumerate(tasks, 1):
        print(f"  [{i}] {t.skill} -- {t.description}")

    for i, task in enumerate(tasks, 1):
        print(f"\n[EXEC] task {i}/{len(tasks)}: {task.skill}")
        print(f"  desc: {task.description}")
        try:
            result = registry.run(task.skill, **task.params)
            if "error" in result.lower() or "unknown skill" in result.lower():
                print(f"  [WARN] {result}")
            else:
                print(f"  [OK] {result}")
        except Exception:
            print(f"  [ERROR] skill failed:\n{traceback.format_exc()}")

    print("[DONE] all tasks completed")


if __name__ == "__main__":
    main()
