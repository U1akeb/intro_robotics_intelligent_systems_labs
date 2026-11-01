#!/usr/bin/env python3
"""Action server that rotates the robot on the spot for a specified angle in radians.
Measures rotation using wheel odometry, handles angle wrapping, and supports cancellation."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    """Calculate yaw from quaternion orientation."""
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_difference(target, current):
    """target - current wrapped to [-pi, pi]."""
    return math.atan2(math.sin(target - current), math.cos(target - current))


class RotateServer(Node):

    def __init__(self):
        super().__init__("rotate_server")
        self.declare_parameter("turn_speed", 0.5)

        self.yaw = None
        group = ReentrantCallbackGroup()

        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Odometry, "odom", self.on_odom, 10, callback_group=group)

        self.action_server = ActionServer(
            self,
            Rotate,
            "rotate",
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda goal_handle: CancelResponse.ACCEPT,
            callback_group=group,
        )

        self.get_logger().info("rotate_server initialized and serving /rotate")

    def on_odom(self, msg: Odometry):
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def on_goal(self, goal):
        # Reject goal if angle is zero or odometry has not yet arrived
        if abs(goal.angle) < 1e-4 or self.yaw is None:
            self.get_logger().warn("Rejecting rotate goal (zero angle or no odom)")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def execute(self, goal_handle):
        target_angle = goal_handle.request.angle
        target_abs = abs(target_angle)
        turn_dir = 1.0 if target_angle > 0 else -1.0
        turn_speed = float(self.get_parameter("turn_speed").value)

        last_yaw = self.yaw
        total_turned = 0.0

        feedback = Rotate.Feedback()
        result = Rotate.Result()

        twist = Twist()
        twist.angular.z = turn_dir * turn_speed

        self.get_logger().info(f"Rotating {target_angle:.2f} rad at {turn_speed:.2f} rad/s")

        while rclpy.ok():
            if self.yaw is not None and last_yaw is not None:
                delta = angle_difference(self.yaw, last_yaw)
                total_turned += abs(delta)
                last_yaw = self.yaw

            # Check if canceled
            if goal_handle.is_cancel_requested:
                self.cmd_vel_pub.publish(Twist())
                goal_handle.canceled()
                result.turned = total_turned * turn_dir
                self.get_logger().info(f"Rotation canceled after {total_turned:.2f} rad")
                return result

            # Check if target reached
            if total_turned >= target_abs:
                break

            self.cmd_vel_pub.publish(twist)
            feedback.turned = total_turned * turn_dir
            goal_handle.publish_feedback(feedback)
            time.sleep(0.02)

        # Stop robot
        self.cmd_vel_pub.publish(Twist())
        goal_handle.succeed()
        result.turned = total_turned * turn_dir
        self.get_logger().info(f"Rotate finished successfully, turned {result.turned:.2f} rad")
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
