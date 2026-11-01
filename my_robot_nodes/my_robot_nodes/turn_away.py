#!/usr/bin/env python3
"""Node that drives the robot forward and turns away from obstacles.
Supports parameters, status reporting, enabling/disabling service, and speed configuration."""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed


class TurnAway(Node):

    def __init__(self):
        super().__init__("turn_away")

        # Step 3 & 5: Declare parameters
        self.declare_parameter("forward_speed", 0.2)
        self.declare_parameter("turn_speed", 0.5)
        self.declare_parameter("max_turn_speed", 1.5)

        # Step 5: Node starts switched off
        self.enabled = False

        # Step 2 & 4: Publishers and Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.status_pub = self.create_publisher(RobotStatus, "robot_status", 10)
        self.create_subscription(ObstacleInfo, "obstacle", self.on_obstacle, 10)

        # Step 5: Services
        self.create_service(SetBool, "turn_away_enable", self.on_enable)
        self.create_service(SetTurnSpeed, "set_turn_speed", self.on_set_turn_speed)

        self.get_logger().info("turn_away node initialized (disabled by default)")

    def on_obstacle(self, msg: ObstacleInfo):
        # Step 3: Read parameters each time a message arrives so changes take effect immediately
        forward_speed = float(self.get_parameter("forward_speed").value)
        turn_speed = float(self.get_parameter("turn_speed").value)

        status_msg = RobotStatus()
        status_msg.obstacle_distance = float(msg.distance)

        # Step 5: While switched off, state is "stopped" and publish no velocities
        if not self.enabled:
            status_msg.state = "stopped"
            self.status_pub.publish(status_msg)
            return

        twist = Twist()
        if not msg.too_close:
            # Step 2: Drive forward
            status_msg.state = "forward"
            twist.linear.x = forward_speed
            twist.angular.z = 0.0
        else:
            # Step 2: Turn on the spot away from the obstacle
            status_msg.state = "turning"
            twist.linear.x = 0.0
            # angle is positive when the obstacle is to the left, so turn right (negative angular.z)
            if msg.angle > 0.0:
                twist.angular.z = -turn_speed
            else:
                twist.angular.z = turn_speed

        self.cmd_vel_pub.publish(twist)
        self.status_pub.publish(status_msg)

    def on_enable(self, request, response):
        if request.data:
            self.enabled = True
            response.success = True
            response.message = "turn_away enabled"
        else:
            self.enabled = False
            # Step 5: Publish one zero velocity when switched off
            self.cmd_vel_pub.publish(Twist())
            response.success = True
            response.message = "turn_away disabled and stopped"

        self.get_logger().info(response.message)
        return response

    def on_set_turn_speed(self, request, response):
        max_turn_speed = float(self.get_parameter("max_turn_speed").value)
        if not (0.0 < request.turn_speed <= max_turn_speed):
            response.success = False
            response.message = (
                f"turn_speed must be > 0 and <= {max_turn_speed:.2f} rad/s"
            )
        else:
            self.set_parameters([Parameter("turn_speed", value=float(request.turn_speed))])
            response.success = True
            response.message = f"turn_speed set to {request.turn_speed:.2f} rad/s"

        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
