from __future__ import annotations

from robomind.config.loader import (
    load_body_config,
    load_brain_config,
    load_task_planner_prompt,
)


def test_load_body_config() -> None:
    config = load_body_config()
    assert config.robot.type == "Fetch"
    assert config.og_config["scene"]["type"] == "InteractiveTraversableScene"
    assert config.timing.odom_publish_every_n_steps == 3


def test_load_brain_config() -> None:
    config = load_brain_config()
    assert config.llm.backend == "deepseek"
    assert config.vlm.backend in {"qwen", "deepseek", "openai"}
    assert config.logging.file == "logs/brain.log"


def test_load_task_planner_prompt() -> None:
    prompt = load_task_planner_prompt()
    assert "JSON" in prompt
    assert "navigate" in prompt
