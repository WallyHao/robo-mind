from __future__ import annotations

import numpy as np
import pytest

from robomind.comm.types import BBox, find_rgb_obs, to_numpy_rgb


class TestBBox:
    def test_center(self) -> None:
        box = BBox(x1=0, y1=0, x2=100, y2=50)
        assert box.center_x == 50.0

    def test_width(self) -> None:
        box = BBox(x1=10, y1=20, x2=90, y2=80)
        assert box.width == 80.0


class TestToNumpyRgb:
    def test_passthrough_uint8(self) -> None:
        array = np.zeros((4, 5, 3), dtype=np.uint8)
        result = to_numpy_rgb(array)
        assert result.dtype == np.uint8
        assert result.shape == (4, 5, 3)

    def test_scales_unit_float(self) -> None:
        result = to_numpy_rgb(np.ones((2, 2, 3), dtype=np.float32))
        assert result.dtype == np.uint8
        assert int(result.max()) == 255

    def test_drops_alpha_channel(self) -> None:
        result = to_numpy_rgb(np.zeros((2, 2, 4), dtype=np.uint8))
        assert result.shape == (2, 2, 3)

    def test_rejects_non_image_shape(self) -> None:
        with pytest.raises(ValueError):
            to_numpy_rgb(np.zeros((2, 2), dtype=np.uint8))


class TestFindRgbObs:
    def test_finds_nested_rgb(self) -> None:
        obs = {"agent": {"obs": {"rgb": np.zeros((1, 1, 3), dtype=np.uint8)}}}
        match = find_rgb_obs(obs)
        assert match is not None
        path, value = match
        assert path.endswith("rgb")
        assert value is obs["agent"]["obs"]["rgb"]

    def test_returns_none_when_absent(self) -> None:
        assert find_rgb_obs({"agent": {"depth": 1}}) is None
