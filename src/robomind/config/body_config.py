from __future__ import annotations

from pydantic import BaseModel, Field


class SceneConfig(BaseModel):
    type: str = Field(default="InteractiveTraversableScene")
    scene_model: str = Field(default="Rs_int")


class RobotConfig(BaseModel):
    type: str = Field(default="Fetch")
    obs_modalities: list[str] = Field(default_factory=lambda: ["rgb"])
    action_type: str = Field(default="continuous")
    action_normalize: bool = Field(default=True)


class EnvConfig(BaseModel):
    canvas_width: int = Field(default=640, ge=320, le=1920)
    canvas_height: int = Field(default=480, ge=240, le=1080)


class TimingConfig(BaseModel):
    odom_publish_every_n_steps: int = Field(default=3, ge=1, le=30)
    camera_publish_every_n_steps: int = Field(default=10, ge=1, le=60)
    velocity_decay: float = Field(default=0.9, ge=0.0, le=1.0)


class LcmChannel(BaseModel):
    channel: str


class LcmPublishConfig(BaseModel):
    channel: str


class LcmPublishOdomConfig(BaseModel):
    channel: str = "/odom"


class LcmPublishCameraConfig(BaseModel):
    channel: str = "/camera_rgb"
    rate_hz: int = Field(default=6, ge=1, le=30)
    jpeg_quality: int = Field(default=75, ge=10, le=100)


class BodyLcmConfig(BaseModel):
    subscribe: list[LcmChannel] = Field(default_factory=list)
    publish_odom: LcmPublishOdomConfig = Field(default_factory=LcmPublishOdomConfig)
    publish_camera: LcmPublishCameraConfig = Field(default_factory=LcmPublishCameraConfig)


class BodyConfig(BaseModel):
    scene: SceneConfig = Field(default_factory=SceneConfig)
    robot: RobotConfig = Field(default_factory=RobotConfig)
    env: EnvConfig = Field(default_factory=EnvConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)
    lcm: BodyLcmConfig = Field(default_factory=BodyLcmConfig)

    @property
    def og_config(self) -> dict[str, object]:
        return {
            "scene": {
                "type": self.scene.type,
                "scene_model": self.scene.scene_model,
            },
            "robots": [
                {
                    "type": self.robot.type,
                    "obs_modalities": self.robot.obs_modalities,
                    "action_type": self.robot.action_type,
                    "action_normalize": self.robot.action_normalize,
                }
            ],
            "env": {
                "canvas_width": self.env.canvas_width,
                "canvas_height": self.env.canvas_height,
            },
        }
