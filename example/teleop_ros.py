#!/usr/bin/env python3
"""ROS node bridging MediaPipe hand landmarks to wuji hand trajectory controllers.

Subscribes to scale-normalized MediaPipe landmark topics published by
er_mediapipe_hand_tracking, runs wuji retargeting to convert (21,3) hand
landmarks into 20 joint angles, and publishes a JointTrajectory command
to the wuji trajectory controller.

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
from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wuji_retargeting import Retargeter  # noqa: E402

NUM_FINGERS = 5
JOINTS_PER_FINGER = 4
NUM_JOINTS = NUM_FINGERS * JOINTS_PER_FINGER


def build_joint_names(side):
    """Build the ordered list of 20 joint names for the trajectory controller.

    Retargeter qpos indices map 1:1 to these names because both use the same
    ordering: Pinocchio reads joints from the URDF in document order
    (finger{1-5}_joint{1-4}), and the ROS controllers follow that same naming.
    """
    joint_names = []
    for finger in range(1, NUM_FINGERS + 1):
        for joint in range(1, JOINTS_PER_FINGER + 1):
            joint_names.append(f"{side}_finger{finger}_joint{joint}")
    return joint_names


def make_landmark_callback(retargeter, trajectory_publisher, joint_names):
    """Return a callback that retargets landmarks and publishes a JointTrajectory."""
    def callback(msg):
        if len(msg.data) != 63:
            rospy.logwarn_throttle(
                5.0,
                f"Expected 63 landmark values, got {len(msg.data)}"
            )
            return

        landmarks = np.array(msg.data, dtype=np.float64).reshape(21, 3)
        qpos = retargeter.retarget(landmarks)

        trajectory = JointTrajectory()
        trajectory.joint_names = joint_names

        point = JointTrajectoryPoint()
        point.positions = qpos.tolist()
        point.time_from_start = rospy.Duration(0.05)
        trajectory.points = [point]

        trajectory_publisher.publish(trajectory)

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
        joint_names = build_joint_names(side)

        traj_topic = f"/{side}_wuji/{side}_wuji_traj_controller/command"
        traj_publisher = rospy.Publisher(traj_topic, JointTrajectory, queue_size=1)

        landmark_topic = f"{args.landmark_ns}/{side}_hand_landmarks"
        rospy.Subscriber(
            landmark_topic,
            Float64MultiArray,
            make_landmark_callback(retargeter, traj_publisher, joint_names),
            queue_size=1
        )
        rospy.loginfo(f"Subscribed to {landmark_topic} -> {traj_topic}")

    rospy.loginfo("Wuji retargeting bridge running")
    rospy.spin()


if __name__ == "__main__":
    main()
