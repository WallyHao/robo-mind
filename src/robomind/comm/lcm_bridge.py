from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import lcm

from .types import Odometry, RoboImage, Twist

logger = logging.getLogger(__name__)


class LcmBridge:
    """Manages LCM pub/sub with a dedicated handler thread.

    Shared by both body.py (sub /cmd_vel, pub /odom + /camera_rgb)
    and brain.py (sub /odom + /camera_rgb, pub /cmd_vel).
    """

    def __init__(self, *, body_mode: bool = False) -> None:
        self._lc = lcm.LCM()
        self._body_mode = body_mode
        self._running = True

        self._latest_odom: Odometry | None = None
        self._latest_image: RoboImage | None = None
        self._odom_lock = threading.Lock()
        self._image_lock = threading.Lock()

        if body_mode:
            self._action: list[float] | None = None
            self._action_lock = threading.Lock()

    # ---- subscribe ----

    def sub_odom(self) -> None:
        self._lc.subscribe("/odom", self._on_odom)

    def sub_camera(self) -> None:
        self._lc.subscribe("/camera_rgb", self._on_camera)

    def sub_cmd_vel(self, callback: Callable[[Twist], None] | None = None) -> None:
        if self._body_mode and callback is None:

            def store_action(_channel: str, data: bytes) -> None:
                try:
                    msg = Twist.lcm_decode(data)
                    if self._action is not None:
                        with self._action_lock:
                            self._action[0] = msg.linear.x * 5.0
                            self._action[1] = msg.angular.z * 3.0
                except Exception:
                    logger.warning("cmd_vel decode failed", exc_info=True)

            self._lc.subscribe("/cmd_vel", store_action)
        elif callback is not None:
            self._lc.subscribe("/cmd_vel", lambda _c, d: callback(Twist.lcm_decode(d)))

    # ---- publish ----

    def pub_odom(self, odom: Odometry) -> None:
        self._lc.publish("/odom", odom.lcm_encode())

    def pub_camera(self, image: RoboImage, *, jpeg_quality: int = 75) -> None:
        try:
            data = image.lcm_jpeg_encode(quality=jpeg_quality)
        except Exception:
            logger.warning("camera jpeg encode failed, falling back to raw", exc_info=True)
            data = image.lcm_encode()
        self._lc.publish("/camera_rgb", data)

    def pub_cmd_vel(self, twist: Twist) -> None:
        self._lc.publish("/cmd_vel", twist.lcm_encode())

    def pub_cmd_vel_raw(self, linear_x: float, angular_z: float) -> None:
        msg = Twist(linear=[linear_x, 0.0, 0.0], angular=[0.0, 0.0, angular_z])
        self.pub_cmd_vel(msg)

    # ---- internal ----

    def _on_odom(self, _channel: str, data: bytes) -> None:
        try:
            msg = Odometry.lcm_decode(data)
            with self._odom_lock:
                self._latest_odom = msg
        except Exception:
            pass

    def _on_camera(self, _channel: str, data: bytes) -> None:
        try:
            msg = RoboImage.lcm_jpeg_decode(data)
            with self._image_lock:
                self._latest_image = msg
        except Exception:
            pass

    def start(self) -> None:
        t = threading.Thread(target=self._spin, daemon=True, name="lcm-spin")
        t.start()

    def _spin(self) -> None:
        while self._running:
            try:
                self._lc.handle_timeout(10)
            except Exception:
                time.sleep(0.005)

    def stop(self) -> None:
        self._running = False

    # ---- accessors (thread-safe) ----

    def get_odom(self) -> Odometry | None:
        with self._odom_lock:
            return self._latest_odom

    def get_image(self) -> RoboImage | None:
        with self._image_lock:
            return self._latest_image

    def set_action(self, action_array: list[float]) -> None:
        self._action = action_array

    def get_action(self) -> list[float] | None:
        if self._action is None:
            return None
        with self._action_lock:
            return list(self._action)

    def apply_decay(self, factor: float) -> None:
        if self._action is not None:
            with self._action_lock:
                self._action[0] *= factor
                self._action[1] *= factor
