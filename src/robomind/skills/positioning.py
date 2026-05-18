from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robomind.comm.lcm_bridge import LcmBridge


class GetPositionSkill:
    name = "get_position"

    def __init__(self, lcm: LcmBridge) -> None:
        self._lcm = lcm

    def execute(self, **kwargs: object) -> str:
        odom = self._lcm.get_odom()
        if odom is None:
            return "no odometry data yet, check if body.py is running"
        return (
            f"position: x={odom.x:.3f}, y={odom.y:.3f}, z={odom.z:.3f}\n"
            f"  yaw: {odom.yaw:.3f} rad"
        )
