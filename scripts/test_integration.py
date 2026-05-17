"""Integration test script for RoboMind modules."""
import sys
import os

dimos_path = os.environ.get("DIMOS_SITE_PATH", "")
if dimos_path and dimos_path not in sys.path:
    sys.path.insert(0, dimos_path)

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

passed = 0
failed = 0


def check(desc: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS: {desc}")
    else:
        failed += 1
        print(f"FAIL: {desc} — {detail}")


# --- Test Config ---
from robomind.config.loader import load_body_config, load_brain_config, load_task_planner_prompt

body_cfg = load_body_config()
check("config body scene_model", body_cfg.scene.scene_model == "Rs_int")

brain_cfg = load_brain_config()
check("config brain llm backend", brain_cfg.llm.backend == "deepseek")
check("config brain vlm backend", brain_cfg.vlm.backend == "qwen")

prompt = load_task_planner_prompt()
check("config prompt length > 500", len(prompt) > 500)
check("config prompt has navigate", "navigate" in prompt)
check("config prompt has navigate_to_object", "navigate_to_object" in prompt)

# --- Test Comm Types ---
from robomind.comm.types import Task, BBox

t = Task(skill="stop", params={}, description="halt")
check("comm Task skill", t.skill == "stop")

b = BBox(0, 0, 100, 50)
check("comm BBox center", b.center_x == 50.0, str(b.center_x))
check("comm BBox width", b.width == 100.0, str(b.width))

# --- Test LLM Errors ---
from robomind.llm.errors import LLMParseError, LLMError, RoboMindError, VLMNotConfiguredError, LCMConnectionError

check("errors LLMParseError < LLMError", issubclass(LLMParseError, LLMError))
check("errors LLMError < RoboMindError", issubclass(LLMError, RoboMindError))
check("errors VLMNotConfigured", issubclass(VLMNotConfiguredError, RoboMindError))
check("errors LCMConnection", issubclass(LCMConnectionError, RoboMindError))

# --- Test Planner ---
from robomind.llm.planner import TaskPlanner

planner = TaskPlanner(system_prompt="test", backend="deepseek")

stripped = planner._strip_markdown_fence('```json\n[{"skill":"stop"}]\n```')
check("planner strip markdown json fence", stripped == '[{"skill":"stop"}]', repr(stripped))

stripped2 = planner._strip_markdown_fence('```\n[{"skill":"turn"}]\n```')
check("planner strip plain fence", stripped2 == '[{"skill":"turn"}]', repr(stripped2))

stripped3 = planner._strip_markdown_fence('[{"skill":"look"}]')
check("planner strip no fence", stripped3 == '[{"skill":"look"}]', repr(stripped3))

# --- Test Skill Registry ---
from robomind.skills.registry import SkillRegistry
from robomind.skills.navigation import StopSkill
from robomind.skills.positioning import GetPositionSkill


class FakeLcm:
    def __init__(self):
        self.published: list[tuple[float, float]] = []

    def pub_cmd_vel_raw(self, lx: float, az: float) -> None:
        self.published.append((lx, az))

    def get_odom(self) -> object | None:
        return None

    def get_image(self) -> object | None:
        return None


fake = FakeLcm()
reg = SkillRegistry()
reg.register(StopSkill(fake))

check("registry list skills", reg.list_skills() == ["stop"], str(reg.list_skills()))

result = reg.run("stop")
check("registry run stop", result == "halted", result)
check("registry stop published zero", fake.published == [(0.0, 0.0)], str(fake.published))

result = reg.run("nonexistent")
check("registry unknown skill", "unknown skill" in result.lower(), result)

# --- Test GetPositionSkill ---
pos_skill = GetPositionSkill(fake)
result = pos_skill.execute()
check("positioning no odom", "no odometry" in result.lower(), result)

# --- Summary ---
print()
print(f"{'='*40}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{failed} TEST(S) FAILED")
    sys.exit(1)
