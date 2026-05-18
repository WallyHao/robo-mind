from __future__ import annotations

import logging
import os
from typing import Protocol

from robomind.comm.types import BBox, OpenAICompatibleVlModel, RoboImage

logger = logging.getLogger(__name__)


class VlModelProtocol(Protocol):
    def query(self, image: RoboImage, prompt: str) -> str: ...


def build_vl_model(
    *,
    backend: str = "qwen",
    api_key: str = "",
) -> VlModelProtocol:
    if backend == "qwen":
        key = (
            api_key
            or os.environ.get("ALIBABA_API_KEY", "")
            or os.environ.get("DASHSCOPE_API_KEY", "")
        )
        if not key:
            raise ValueError("ALIBABA_API_KEY or DASHSCOPE_API_KEY required for qwen backend")
        model_name = os.environ.get("QWEN_VL_MODEL", "qwen2.5-vl-72b-instruct")
        base_url = os.environ.get(
            "QWEN_VL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        return OpenAICompatibleVlModel(model_name=model_name, api_key=key, base_url=base_url)

    elif backend == "deepseek":
        key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY required for deepseek backend")
        return OpenAICompatibleVlModel(
            model_name="deepseek-vl2", api_key=key, base_url="https://api.deepseek.com"
        )

    elif backend == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OPENAI_API_KEY required for openai backend")
        return OpenAICompatibleVlModel(
            model_name="gpt-4o", api_key=key, base_url="https://api.openai.com/v1"
        )

    else:
        raise ValueError(f"unknown VLM backend: '{backend}', supported: qwen, deepseek, openai")


_OBJECT_BBOX_PROMPT = (
    "Look at this image. If you see a {query}, describe its bounding box "
    "as [x1, y1, x2, y2] in pixel coordinates. "
    "If you do NOT see it, reply exactly 'NONE'. "
    "Reply ONLY with the coordinates or 'NONE', no other text."
)


def get_object_bbox(
    vl_model: VlModelProtocol,
    image: RoboImage,
    query: str,
) -> BBox | None:
    prompt = _OBJECT_BBOX_PROMPT.format(query=query)
    raw = vl_model.query(image, prompt).strip()

    if raw.upper() == "NONE":
        return None

    import re

    numbers = re.findall(r"\d+", raw)
    if len(numbers) >= 4:
        x1, y1, x2, y2 = map(float, numbers[:4])
        return BBox(x1=x1, y1=y1, x2=x2, y2=y2)

    logger.warning("VLM returned unparseable bbox: %s", raw)
    return None
