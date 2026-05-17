from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from robomind.llm.vl_model import VlModelProtocol, get_object_bbox

from .base import Skill

if TYPE_CHECKING:
    from robomind.comm.lcm_bridge import LcmBridge

logger = logging.getLogger(__name__)


class LookSkill:
    name = "look"

    def __init__(self, lcm: LcmBridge, vl_model: VlModelProtocol) -> None:
        self._lcm = lcm
        self._vl_model = vl_model

    def execute(self, query: str = "") -> str:
        image = self._lcm.get_image()
        if image is None:
            return "no camera frame received yet, check if body.py is running"

        bbox = get_object_bbox(self._vl_model, image, query)
        if bbox is None:
            return f"'{query}' not found in current frame"

        cx = bbox.center_x
        offset = (cx - image.width / 2) / image.width
        side = "right" if offset < 0 else "left" if offset > 0 else "center"
        return (
            f"found '{query}': bbox=[{bbox.x1:.0f},{bbox.y1:.0f},{bbox.x2:.0f},{bbox.y2:.0f}]\n"
            f"  offset: {offset:+.2f} ({side})"
        )


class NavigateToObjectSkill:
    name = "navigate_to_object"

    def __init__(self, lcm: LcmBridge, vl_model: VlModelProtocol) -> None:
        self._lcm = lcm
        self._vl_model = vl_model

    def execute(self, query: str = "", max_steps: int = 10) -> str:
        if self._lcm.get_image() is None:
            return "no camera frame received yet, check if body.py is running"

        lines = [f"visual navigation target: '{query}'"]

        for step in range(max_steps):
            time.sleep(0.3)
            image = self._lcm.get_image()
            if image is None:
                continue

            bbox = get_object_bbox(self._vl_model, image, query)
            if bbox is None:
                lines.append(f"  [{step + 1}] target not found, searching left...")
                self._lcm.pub_cmd_vel_raw(0.0, 0.4)
                time.sleep(0.8)
                self._lcm.pub_cmd_vel_raw(0.0, 0.0)
                continue

            cx = bbox.center_x
            size_ratio = bbox.width / image.width
            offset = (cx - image.width / 2) / image.width
            lines.append(f"  [{step + 1}] size={size_ratio:.2f} offset={offset:+.2f}")

            if size_ratio > 0.30:
                self._lcm.pub_cmd_vel_raw(0.0, 0.0)
                lines.append(f"arrived near '{query}'")
                odom = self._lcm.get_odom()
                if odom:
                    lines.append(f"  final position: ({odom.x:.2f}, {odom.y:.2f})")
                return "\n".join(lines)

            angular = -offset * 1.5
            linear = 0.3 if abs(offset) < 0.15 else 0.1
            self._lcm.pub_cmd_vel_raw(linear, angular)
            time.sleep(0.5)
            self._lcm.pub_cmd_vel_raw(0.0, 0.0)

        self._lcm.pub_cmd_vel_raw(0.0, 0.0)
        lines.append(f"max steps ({max_steps}) reached, navigation ended")
        return "\n".join(lines)
