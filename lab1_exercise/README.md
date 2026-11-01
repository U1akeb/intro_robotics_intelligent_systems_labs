# Lab 1 Exercise: Program diffdrive_bot

**Student:** Bekalu (ulakeb)  
**Program:** BSc in Software Engineering, Addis Ababa University  
**Course:** Introduction to Robotics and Intelligent Systems (Academic Year 2026)  
**Lecturer / Lab Assistant:** Mohammed Sraj (MSc AI)  

---

## Overview

This repository contains the complete solution for **Lab 1: ROS 2 and Custom Robot Simulation**. It contains four packages designed to build standalone in the `src/` directory of any ROS 2 workspace:

| Package | Build Type | Description |
|---|---|---|
| `diffdrive_bot` | `ament_cmake` | Modified robot URDF with added rear depth camera and IMU, Gazebo obstacle world, and simulation launch files. |
| `lab_interfaces` | `ament_cmake` | Base interfaces (`ObstacleInfo.msg`, `SetSpeed.srv`, `DriveDistance.action`). |
| `my_robot_interfaces` | `ament_cmake` | Custom interfaces developed for this exercise (`RobotStatus.msg`, `SetTurnSpeed.srv`, `Rotate.action`). |
| `my_robot_nodes` | `ament_python` | Python nodes and launch files (`turn_away`, `rotate_server`, `square_driver`, and `square.launch.py`). |

---

## Building the Workspace

1. Ensure ROS 2 environment is sourced (make sure active conda environments are deactivated):
   ```bash
   conda deactivate
   source /opt/ros/jazzy/setup.bash
   ```

2. From your workspace root (e.g., `~/ros2_ws`):
   ```bash
   cd ~/ros2_ws
   colcon build --symlink-install
   source install/setup.bash
   ```

---

## Step-by-Step Instructions & Verification

### Step 1: Depth Camera and IMU
- **What was added:**
  - `depth_camera_link` positioned at the rear of `base_link` (`-0.215 m`, rotated $\pi$ rad about $Z$).
  - `imu_link` centered at `base_link` (`0 0 0`).
  - Gazebo sensor plugins for depth camera (10 Hz, 320x240, `R_FLOAT32`) and IMU (50 Hz).
  - ROS-Gazebo bridge configured in `config/bridge.yaml`.
- **Verification:**
  1. Check transform coordinates:
     ```bash
     ros2 run tf2_ros tf2_echo base_link depth_camera_link
     ```
     *Output shows translation `[-0.215, 0, 0]` and rotation half a turn.*
  2. Launch simulation and RViz:
     ```bash
     ros2 launch diffdrive_bot gazebo.launch.py
     ```
  3. Verify IMU frequency:
     ```bash
     ros2 topic hz /imu
     # Output: ~50 Hz
     ```
  4. In RViz, add an **Image** display for `/depth_camera/image` and a **PointCloud2** display for `/depth_camera/points`.

---

### Step 2, 3, 4, 5: The `turn_away` Node
- **Features:**
  - **Step 2:** Subscribes to `/obstacle` and publishes velocity commands to `/cmd_vel` (drives forward when clear, turns away when obstacle detected).
  - **Step 3:** Dynamic parameters `forward_speed` (default 0.2 m/s) and `turn_speed` (default 0.5 rad/s).
  - **Step 4:** Publishes state on `/robot_status` (`my_robot_interfaces/msg/RobotStatus`).
  - **Step 5:** Services `/turn_away_enable` (`std_srvs/srv/SetBool`) and `/set_turn_speed` (`my_robot_interfaces/srv/SetTurnSpeed`).
- **How to Run & Test:**
  1. Terminal 1 (Start simulation with obstacle detector):
     ```bash
     ros2 launch diffdrive_bot control.launch.py
     ```
  2. Terminal 2 (Run `turn_away` node):
     ```bash
     ros2 run my_robot_nodes turn_away
     ```
  3. Terminal 3 (Control & Inspect):
     ```bash
     # Enable the node to start driving:
     ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"

     # Inspect status topic:
     ros2 topic echo /robot_status

     # Change speed dynamically via service:
     ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 0.8}"

     # Change forward speed via parameter:
     ros2 param set /turn_away forward_speed 0.35

     # Disable the node (stops the robot):
     ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: false}"
     ```

---

### Step 6: Action Server (`rotate_server`)
- **Features:**
  - Action server on `/rotate` (`my_robot_interfaces/action/Rotate`).
  - Tracks yaw from `/odom` and accurately handles angle wrap-around at $\pm\pi$.
  - Publishes real-time feedback and supports cancellation.
- **How to Run & Test:**
  1. Terminal 1 (Start simulation):
     ```bash
     ros2 launch diffdrive_bot gazebo.launch.py
     ```
  2. Terminal 2 (Start rotate action server):
     ```bash
     ros2 run my_robot_nodes rotate_server
     ```
  3. Terminal 3 (Send goal):
     ```bash
     ros2 action send_goal --feedback /rotate my_robot_interfaces/action/Rotate "{angle: 1.57}"
     ```
     *The robot rotates 90° counter-clockwise, and feedback counts up to ~1.57 rad.*

---

### Step 7: Complete Square Driving (`square.launch.py`)
- **Features:**
  - `square_driver` acts as an action client to `/drive_distance` and `/rotate`, executing 4 sides of length `side_length` (default 0.5 m) separated by 90-degree left turns.
  - `square.launch.py` launches Gazebo, RViz, detector, `drive_distance_server`, `rotate_server`, and `square_driver` in a single command.
- **How to Run:**
  ```bash
  ros2 launch my_robot_nodes square.launch.py side_length:=0.8
  ```
  *The robot autonomously drives an 0.8 m square and returns to its initial spot.*

---

## Required Screenshots for Submission

1. **RViz Depth Camera Display** (`screenshots/rviz_depth_camera.png`):
   - Shows `/depth_camera/image` and `/depth_camera/points` visualizing the wall behind the robot.
2. **rqt_graph** (`screenshots/rqt_graph_square.png`):
   - Shows the active nodes and topic/action connections while `square.launch.py` is running:
     ```bash
     ros2 run rqt_graph rqt_graph
     ```

---

## Notes & Observations
- **Anaconda Python Collision:** If Anaconda is in `PATH`, `rosidl_adapter` may fail due to Python path mismatches. Deactivating conda or specifying `-DPython3_EXECUTABLE=/usr/bin/python3` during `colcon build` guarantees clean compilation.
- **Angle Wrap-around:** Because yaw angles jump between $+\pi$ and $-\pi$ when facing backwards, computing heading changes via consecutive differences (`angle_difference`) rather than subtracting the initial yaw ensures continuous and reliable rotation tracking.
