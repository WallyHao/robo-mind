from __future__ import annotations

import pytest

from robomind.llm.vl_model import build_vl_model, get_object_bbox


class _FakeVlModel:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def query(self, _image: object, _prompt: str) -> str:
        return self.reply


class TestGetObjectBbox:
    def test_parses_coordinates(self) -> None:
        bbox = get_object_bbox(_FakeVlModel("[10, 20, 110, 60]"), object(), "door")
        assert bbox is not None
        assert (bbox.x1, bbox.y1, bbox.x2, bbox.y2) == (10, 20, 110, 60)

    def test_none_reply_returns_none(self) -> None:
        assert get_object_bbox(_FakeVlModel("NONE"), object(), "door") is None

    def test_unparseable_reply_returns_none(self) -> None:
        assert get_object_bbox(_FakeVlModel("maybe later"), object(), "door") is None


class TestBuildVlModel:
    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown VLM backend"):
            build_vl_model(backend="nope")

    def test_missing_qwen_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ALIBABA_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ALIBABA_API_KEY"):
            build_vl_model(backend="qwen")

    def test_openai_backend_requires_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            build_vl_model(backend="openai")
