from __future__ import annotations

from robomind.comm.types import BBox


class TestBBox:
    def test_center(self) -> None:
        box = BBox(x1=0, y1=0, x2=100, y2=50)
        assert box.center_x == 50.0

    def test_width(self) -> None:
        box = BBox(x1=10, y1=20, x2=90, y2=80)
        assert box.width == 80.0
