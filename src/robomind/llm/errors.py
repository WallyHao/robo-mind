from __future__ import annotations


class RoboMindError(Exception):
    pass


class ConfigError(RoboMindError):
    pass


class LLMError(RoboMindError):
    pass


class LLMParseError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


class VLMNotConfiguredError(RoboMindError):
    pass


class LCMConnectionError(RoboMindError):
    pass
