from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from .base import Skill

if TYPE_CHECKING:
    from robomind.comm.lcm_bridge import LcmBridge

logger = logging.getLogger(__name__)


class NavigateSkill:
    name = "navigate"

    def __init__(self, lcm: LcmBridge) -> None:
        self._lcm = lcm

    def execute(
        self,
        query: str = "",
        duration: float = 3.0,
        linear_x: float = 0.3,
        angular_z: float = 0.0,
    ) -> str:
        lines = [f"navigate: '{query}'"]
        odom = self._lcm.get_odom()
        if odom:
            lines.append(f"  start: ({odom.x:.2f}, {odom.y:.2f})")

        end_time = time.time() + duration
        while time.time() < end_time:
            self._lcm.pub_cmd_vel_raw(linear_x, angular_z)
            time.sleep(0.1)

        self._lcm.pub_cmd_vel_raw(0.0, 0.0)

        odom = self._lcm.get_odom()
        if odom:
            lines.append(f"  end: ({odom.x:.2f}, {odom.y:.2f})")
        lines.append("navigate done")
        return "\n".join(lines)


class StopSkill:
    name = "stop"

    def __init__(self, lcm: LcmBridge) -> None:
        self._lcm = lcm

    def execute(self, **kwargs: object) -> str:
        self._lcm.pub_cmd_vel_raw(0.0, 0.0)
        return "halted"


class TurnSkill:
    name = "turn"

    def __init__(self, lcm: LcmBridge) -> None:
        self._lcm = lcm

    def execute(self, direction: str = "left", duration: float = 1.5) -> str:
        angular_z = 0.5 if direction == "left" else -0.5
        end_time = time.time() + duration
        while time.time() < end_time:
            self._lcm.pub_cmd_vel_raw(0.0, angular_z)
            time.sleep(0.1)
        self._lcm.pub_cmd_vel_raw(0.0, 0.0)
        return f"turned {direction} for {duration}s"
