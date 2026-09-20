from __future__ import annotations

import sys
import types

import pytest

from robomind.comm import lcm_bridge


class _FakeLCM:
    def __init__(self) -> None:
        self.subscriptions: dict[str, object] = {}
        self.published: list[tuple[str, bytes]] = []

    def subscribe(self, channel: str, handler: object) -> None:
        self.subscriptions[channel] = handler

    def publish(self, channel: str, data: bytes) -> None:
        self.published.append((channel, data))

    def handle_timeout(self, _timeout: int) -> None:
        return None


class _FakeTwist:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def lcm_encode(self) -> bytes:
        return b"twist"


@pytest.fixture
def fake_lcm(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    module = types.ModuleType("lcm")
    module.LCM = _FakeLCM  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "lcm", module)
    monkeypatch.setattr(lcm_bridge, "Twist", _FakeTwist)
    return module


def test_pub_cmd_vel_raw_encodes_and_publishes(fake_lcm: types.ModuleType) -> None:
    bridge = lcm_bridge.LcmBridge()
    bridge.pub_cmd_vel_raw(0.5, -0.2)
    assert bridge._lc.published == [("/cmd_vel", b"twist")]


def test_pub_cmd_vel_publishes_encoded_twist(fake_lcm: types.ModuleType) -> None:
    bridge = lcm_bridge.LcmBridge()
    bridge.pub_cmd_vel(_FakeTwist())
    assert bridge._lc.published == [("/cmd_vel", b"twist")]


def test_subscribe_registers_both_channels(fake_lcm: types.ModuleType) -> None:
    bridge = lcm_bridge.LcmBridge()
    bridge.sub_odom()
    bridge.sub_camera()
    assert set(bridge._lc.subscriptions) == {"/odom", "/camera_rgb"}


def test_action_round_trip_and_decay(fake_lcm: types.ModuleType) -> None:
    bridge = lcm_bridge.LcmBridge(body_mode=True)
    bridge.set_action([1.0, 2.0])
    assert bridge.get_action() == [1.0, 2.0]
    bridge.apply_decay(0.5)
    assert bridge.get_action() == [0.5, 1.0]


def test_accessors_start_empty(fake_lcm: types.ModuleType) -> None:
    bridge = lcm_bridge.LcmBridge()
    assert bridge.get_odom() is None
    assert bridge.get_image() is None
