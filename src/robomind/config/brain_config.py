from __future__ import annotations

from pydantic import BaseModel, Field


class LlmConfig(BaseModel):
    backend: str = Field(default="deepseek", pattern=r"^(deepseek)$")
    model: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class VlmBackendConfig(BaseModel):
    model: str
    base_url: str = "https://api.deepseek.com"


class VlmConfig(BaseModel):
    backend: str = Field(default="qwen", pattern=r"^(qwen|deepseek|openai)$")
    qwen: VlmBackendConfig = Field(
        default_factory=lambda: VlmBackendConfig(
            model="qwen2.5-vl-72b-instruct",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )
    deepseek: VlmBackendConfig = Field(
        default_factory=lambda: VlmBackendConfig(model="deepseek-vl2")
    )
    openai: VlmBackendConfig = Field(
        default_factory=lambda: VlmBackendConfig(model="gpt-4o")
    )


class LcmSubscribeChannel(BaseModel):
    channel: str


class LcmPublishCmdVel(BaseModel):
    channel: str = "/cmd_vel"
    linear_scale: float = Field(default=5.0, gt=0.0)
    angular_scale: float = Field(default=3.0, gt=0.0)


class BrainLcmConfig(BaseModel):
    subscribe: list[LcmSubscribeChannel] = Field(default_factory=list)
    publish_cmd_vel: LcmPublishCmdVel = Field(default_factory=LcmPublishCmdVel)


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    file: str = Field(default="logs/brain.log")


class BrainConfig(BaseModel):
    llm: LlmConfig = Field(default_factory=LlmConfig)
    vlm: VlmConfig = Field(default_factory=VlmConfig)
    lcm: BrainLcmConfig = Field(default_factory=BrainLcmConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @property
    def vlm_backend_config(self) -> VlmBackendConfig:
        return getattr(self.vlm, self.vlm.backend)
