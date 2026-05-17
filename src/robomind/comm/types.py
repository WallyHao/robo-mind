from __future__ import annotations

import base64
import dataclasses
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from dimos.msgs.sensor_msgs.Image import Image as RoboImage

# The original project imported dimOS message types by their full paths.
# We re-export them here so the rest of the codebase has a single import source.
# These may raise ImportError if dimOS is not installed — the caller is expected
# to configure sys.path before importing this module.
from dimos.msgs.geometry_msgs.Twist import Twist  # noqa: F401
from dimos.msgs.geometry_msgs.Pose import Pose  # noqa: F401
from dimos.msgs.nav_msgs.Odometry import Odometry  # noqa: F401
from dimos.msgs.sensor_msgs.Image import Image as RoboImage  # noqa: F401
from dimos.msgs.sensor_msgs.Image import ImageFormat  # noqa: F401


@dataclasses.dataclass
class Task:
    skill: str
    params: dict[str, Any]
    description: str = ""


@dataclasses.dataclass
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def width(self) -> float:
        return self.x2 - self.x1


class OpenAICompatibleVlModel:
    """Thin wrapper around OpenAI-compatible VLM APIs (Qwen, DeepSeek, GPT-4o)."""

    def __init__(self, *, model_name: str, api_key: str, base_url: str) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def query(self, image: RoboImage, prompt: str) -> str:
        img_base64 = base64.b64encode(image.to_raw_bytes()).decode()
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ""


def to_numpy_rgb(rgb_value: object) -> np.ndarray:
    """Convert OmniGibson observation to uint8 HxWx3 numpy array."""
    if hasattr(rgb_value, "detach"):
        rgb_value = rgb_value.detach()
    if hasattr(rgb_value, "cpu"):
        rgb_value = rgb_value.cpu()
    if hasattr(rgb_value, "numpy"):
        rgb_value = rgb_value.numpy()

    rgb_array = np.asarray(rgb_value)
    if rgb_array.ndim != 3:
        raise ValueError(f"unexpected rgb ndim={rgb_array.ndim}, shape={rgb_array.shape}")

    if rgb_array.shape[2] == 4:
        rgb_array = rgb_array[:, :, :3]
    elif rgb_array.shape[2] != 3:
        raise ValueError(
            f"unexpected channel count={rgb_array.shape[2]}, shape={rgb_array.shape}"
        )

    if rgb_array.dtype != np.uint8:
        if np.issubdtype(rgb_array.dtype, np.floating):
            max_value = float(np.nanmax(rgb_array)) if rgb_array.size else 0.0
            if max_value <= 1.0:
                rgb_array = rgb_array * 255.0
        rgb_array = np.clip(rgb_array, 0, 255).astype(np.uint8)

    return np.ascontiguousarray(rgb_array)


def find_rgb_obs(obs: dict[str, object], path: str = "obs") -> tuple[str, object] | None:
    """Recursively find the first 'rgb' key in an OmniGibson observation dict."""
    if isinstance(obs, dict):
        if "rgb" in obs and obs["rgb"] is not None:
            return f"{path}.rgb", obs["rgb"]
        for key, child in obs.items():
            result = find_rgb_obs(child, f"{path}.{key}")  # type: ignore[arg-type]
            if result is not None:
                return result
    return None
