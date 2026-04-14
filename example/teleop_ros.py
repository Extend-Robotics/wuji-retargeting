#!/usr/bin/env python3
"""ROS node bridging MediaPipe hand landmarks to wuji hand position controllers.

Subscribes to scale-normalized MediaPipe landmark topics published by
er_mediapipe_hand_tracking, runs wuji retargeting to convert (21,3) hand
landmarks into 20 joint angles, and publishes each joint angle to the
corresponding position controller.

Usage:
    # Right hand only (default)
    python teleop_ros.py

    # Left hand only
    python teleop_ros.py --hand left

    # Both hands
    python teleop_ros.py --hand both

    # Custom landmark topic namespace
    python teleop_ros.py --landmark-ns /hand_tracker
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import rospy
from std_msgs.msg import Float64, Float64MultiArray

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wuji_retargeting import Retargeter  # noqa: E402

NUM_FINGERS = 5
JOINTS_PER_FINGER = 4
NUM_JOINTS = NUM_FINGERS * JOINTS_PER_FINGER

# Retargeter qpos indices map 1:1 to position controllers because both use
# the same ordering: Pinocchio reads joints from the URDF in document order
# (finger{1-5}_joint{1-4}), and the ROS controllers follow that same naming.
CONTROLLER_TOPIC_TEMPLATE = (
    "/{side}_wuji/{side}_finger{finger}_joint{joint}_position_controller/command"
)


def build_controller_publishers(side):
    """Create a Float64 publisher for each of the 20 position controllers."""
    publishers = []
    for finger in range(1, NUM_FINGERS + 1):
        for joint in range(1, JOINTS_PER_FINGER + 1):
            topic = CONTROLLER_TOPIC_TEMPLATE.format(
                side=side, finger=finger, joint=joint
            )
            pub = rospy.Publisher(topic, Float64, queue_size=1)
            publishers.append(pub)
    return publishers


def make_landmark_callback(retargeter, publishers):
    """Return a callback that retargets landmarks and publishes joint angles."""
    def callback(msg):
        if len(msg.data) != 63:
            rospy.logwarn_throttle(
                5.0,
                f"Expected 63 landmark values, got {len(msg.data)}"
            )
            return

        landmarks = np.array(msg.data, dtype=np.float64).reshape(21, 3)
        qpos = retargeter.retarget(landmarks)

        for i, pub in enumerate(publishers):
            pub.publish(Float64(data=float(qpos[i])))

    return callback


def main():
    parser = argparse.ArgumentParser(description="Wuji retargeting ROS bridge")
    parser.add_argument(
        "--hand", choices=["left", "right", "both"], default="right",
        help="Which hand(s) to retarget (default: right)"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to retargeting config YAML (default: config/adaptive_analytical_avp.yaml)"
    )
    parser.add_argument(
        "--landmark-ns", type=str, default="/hand_tracker",
        help="Namespace of the landmark topics (default: /hand_tracker)"
    )

    argv = rospy.myargv(argv=sys.argv)
    args = parser.parse_args(argv[1:])

    rospy.init_node("wuji_retargeting_bridge")

    example_dir = Path(__file__).resolve().parent
    config_path = args.config or str(example_dir / "config" / "adaptive_analytical_avp.yaml")

    sides = ["left", "right"] if args.hand == "both" else [args.hand]

    for side in sides:
        retargeter = Retargeter.from_yaml(config_path, hand_side=side)
        publishers = build_controller_publishers(side)

        landmark_topic = f"{args.landmark_ns}/{side}_hand_landmarks"
        rospy.Subscriber(
            landmark_topic,
            Float64MultiArray,
            make_landmark_callback(retargeter, publishers),
            queue_size=1
        )
        rospy.loginfo(f"Subscribed to {landmark_topic} -> /{side}_wuji/ controllers")

    rospy.loginfo("Wuji retargeting bridge running")
    rospy.spin()


if __name__ == "__main__":
    main()
