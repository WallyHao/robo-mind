from __future__ import annotations

import logging
import os
import sys
from typing import Any, cast

import numpy as np

from robomind.comm.lcm_bridge import LcmBridge
from robomind.comm.types import ImageFormat, Odometry, Pose, RoboImage, find_rgb_obs, to_numpy_rgb
from robomind.config.loader import load_body_config

logger = logging.getLogger("robomind.body")


def _find_dimos_lib() -> str:
    dimos_path = os.environ.get("DIMOS_SITE_PATH", "")
    if dimos_path and os.path.isdir(dimos_path):
        return dimos_path
    raise RuntimeError(
        "cannot find dimOS site-packages. set DIMOS_SITE_PATH in .env file "
        "to point to the installed dimOS package location."
    )


def _setup_imports() -> None:
    for key in ("http_proxy", "https_proxy", "all_proxy", "ALL_PROXY"):
        os.environ.pop(key, None)

    dimos_lib = _find_dimos_lib()
    if dimos_lib not in sys.path:
        sys.path.insert(0, dimos_lib)


def _setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/body.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    _setup_logging()
    _setup_imports()

    import omnigibson as og  # noqa: E402

    config = load_body_config()

    logger.info(
        "initializing OmniGibson: scene=%s robot=%s", config.scene.scene_model, config.robot.type
    )

    env = og.Environment(configs=config.og_config)
    robot = env.robots[0]
    env.reset()

    lcm = LcmBridge(body_mode=True)
    action = np.zeros(robot.action_dim, dtype=np.float64)
    lcm.set_action(list(action))
    lcm.sub_cmd_vel()
    lcm.start()

    camera_source_logged = False
    camera_missing_logged = False
    step_count = 0

    logger.info(
        "body ready | sub=/cmd_vel pub=/odom(~%dHz) pub=/camera_rgb(~%dHz)",
        config.timing.odom_publish_every_n_steps,
        config.timing.camera_publish_every_n_steps,
    )

    try:
        while True:
            raw_action = lcm.get_action()
            action[:] = raw_action if raw_action is not None else np.zeros_like(action)
            obs, _r, _t, _tr, _i = env.step(action)
            step_count += 1

            lcm.apply_decay(config.timing.velocity_decay)

            if step_count % config.timing.odom_publish_every_n_steps == 0:
                _publish_odom(lcm, robot)

            if step_count % config.timing.camera_publish_every_n_steps == 0:
                _publish_camera(
                    lcm,
                    obs,
                    robot,
                    quality=config.lcm.publish_camera.jpeg_quality,
                    source_logged=camera_source_logged,
                    missing_logged=camera_missing_logged,
                )
                camera_source_logged = True

    except KeyboardInterrupt:
        logger.info("shutting down body process")
    finally:
        lcm.stop()
        env.close()


def _publish_odom(lcm: LcmBridge, robot: Any) -> None:
    try:
        pos, ori = robot.get_position_orientation()
        pose = Pose(
            position=[float(pos[0]), float(pos[1]), float(pos[2])],
            orientation=[float(ori[0]), float(ori[1]), float(ori[2]), float(ori[3])],
        )
        odom_msg = Odometry(
            frame_id="odom",
            child_frame_id="base_link",
            pose=pose,
        )
        lcm.pub_odom(odom_msg)
    except Exception:
        logger.debug("odom publish skipped", exc_info=True)


def _publish_camera(
    lcm: LcmBridge,
    obs: dict[str, object],
    robot: Any,
    *,
    quality: int = 75,
    source_logged: bool,
    missing_logged: bool,
) -> None:
    try:
        robot_obs = cast(dict[str, object], obs.get(robot.name, {}))
        rgb_match = find_rgb_obs(robot_obs, f"obs[{robot.name}]")
        if rgb_match is None:
            rgb_match = find_rgb_obs(obs, "obs")

        if rgb_match is None:
            if not missing_logged:
                logger.warning("no RGB observation found in camera frame")
            return

        _rgb_path, rgb_value = rgb_match
        rgb_array = to_numpy_rgb(rgb_value)

        if not source_logged:
            logger.info(
                "camera source: %s, shape=%s, dtype=%s",
                _rgb_path,
                rgb_array.shape,
                rgb_array.dtype,
            )

        img_msg = RoboImage.from_numpy(
            rgb_array,
            format=ImageFormat.RGB,
            frame_id="camera_rgb",
        )
        lcm.pub_camera(img_msg, jpeg_quality=quality)
    except Exception:
        logger.debug("camera publish failed", exc_info=True)


if __name__ == "__main__":
    main()
