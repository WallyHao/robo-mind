"""Test LCM bridge, dimOS message imports, and config generation."""
import sys
import os

dimos_path = os.environ.get("DIMOS_SITE_PATH", "")
if dimos_path and dimos_path not in sys.path:
    sys.path.insert(0, dimos_path)

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

passed = 0
failed = 0

def check(desc, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS: {desc}")
    else:
        failed += 1
        print(f"FAIL: {desc} — {detail}")

# --- dimOS message types ---
from dimos.msgs.geometry_msgs.Twist import Twist
from dimos.msgs.geometry_msgs.Pose import Pose
from dimos.msgs.nav_msgs.Odometry import Odometry
from dimos.msgs.sensor_msgs.Image import Image as RoboImage, ImageFormat

twist = Twist(linear=[0.5, 0.0, 0.0], angular=[0.0, 0.0, 0.3])
data = twist.lcm_encode()
check("dimOS Twist encode", isinstance(data, (bytes, bytearray)), f"type={type(data).__name__}")
decoded = Twist.lcm_decode(data)
check("dimOS Twist roundtrip linear", abs(decoded.linear.x - 0.5) < 0.001)
check("dimOS Twist roundtrip angular", abs(decoded.angular.z - 0.3) < 0.001)

pose = Pose(position=[1.0, 2.0, 0.0], orientation=[0.0, 0.0, 0.0, 1.0])
odom = Odometry(frame_id="odom", child_frame_id="base_link", pose=pose)
data2 = odom.lcm_encode()
check("dimOS Odometry encode", isinstance(data2, (bytes, bytearray)))
decoded2 = Odometry.lcm_decode(data2)
check("dimOS Odometry decode frame_id", decoded2.frame_id == "odom")
check("dimOS Odometry decode pose.x", abs(decoded2.pose.position.x - 1.0) < 0.001)

check("dimOS ImageFormat RGB", ImageFormat.RGB is not None)

# --- BodyConfig og_config generation ---
from robomind.config.loader import load_body_config
body_cfg = load_body_config()
og = body_cfg.og_config
check("body og_config scene", og["scene"]["type"] == "InteractiveTraversableScene")
check("body og_config robots list", isinstance(og["robots"], list) and len(og["robots"]) == 1)
robot = og["robots"][0]
check("body og_config robot type", robot["type"] == "Fetch")
check("body og_config robot modalities", "rgb" in robot["obs_modalities"])
check("body og_config env", og["env"]["canvas_width"] == 640)

# --- lcm_bridge instantiation ---
from robomind.comm.lcm_bridge import LcmBridge
bridge = LcmBridge(body_mode=False)
check("lcm_bridge create", bridge is not None)
check("lcm_bridge get_odom none initially", bridge.get_odom() is None)
check("lcm_bridge get_image none initially", bridge.get_image() is None)

body_bridge = LcmBridge(body_mode=True)
check("lcm_bridge body_mode create", body_bridge is not None)

# --- VLM import ---
from robomind.llm.vl_model import get_object_bbox
check("vlm get_object_bbox imported", get_object_bbox is not None)

print()
print(f"{'='*40}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{failed} TEST(S) FAILED")
    sys.exit(1)
