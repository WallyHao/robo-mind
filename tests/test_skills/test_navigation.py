from __future__ import annotations

from robomind.skills.navigation import NavigateSkill, StopSkill, TurnSkill
from robomind.skills.positioning import GetPositionSkill
from robomind.skills.registry import SkillRegistry


class FakeLcmBridge:
    def __init__(self) -> None:
        self.published: list[tuple[float, float]] = []
        self._odom = None
        self._image = None

    def pub_cmd_vel_raw(self, linear_x: float, angular_z: float) -> None:
        self.published.append((linear_x, angular_z))

    def get_odom(self) -> object | None:
        return self._odom

    def get_image(self) -> object | None:
        return self._image


class TestStopSkill:
    def test_stop_publishes_zero_velocity(self) -> None:
        lcm = FakeLcmBridge()
        skill = StopSkill(lcm)
        result = skill.execute()
        assert result == "halted"
        assert lcm.published == [(0.0, 0.0)]


class TestNavigateSkill:
    def test_zero_duration_stops(self) -> None:
        lcm = FakeLcmBridge()
        result = NavigateSkill(lcm).execute(duration=0.0)
        assert "navigate done" in result
        assert lcm.published == [(0.0, 0.0)]


class TestTurnSkill:
    def test_zero_duration_stops(self) -> None:
        lcm = FakeLcmBridge()
        result = TurnSkill(lcm).execute(direction="left", duration=0.0)
        assert result == "turned left for 0.0s"
        assert lcm.published == [(0.0, 0.0)]


class TestSkillRegistry:
    def test_register_and_list(self) -> None:
        registry = SkillRegistry()
        registry.register(StopSkill(FakeLcmBridge()))
        assert registry.list_skills() == ["stop"]

    def test_run_unknown_skill(self) -> None:
        registry = SkillRegistry()
        result = registry.run("nonexistent", x=1)
        assert "unknown skill" in result

    def test_run_valid_skill(self) -> None:
        lcm = FakeLcmBridge()
        registry = SkillRegistry()
        registry.register(StopSkill(lcm))
        result = registry.run("stop")
        assert result == "halted"


class TestGetPositionSkill:
    def test_no_odom_yet(self) -> None:
        lcm = FakeLcmBridge()
        skill = GetPositionSkill(lcm)
        result = skill.execute()
        assert "no odometry" in result.lower()
