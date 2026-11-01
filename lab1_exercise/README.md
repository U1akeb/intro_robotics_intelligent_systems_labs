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

## Screenshots (Step 1 & Step 7)

### 1. Step 1: RViz Depth Camera & PointCloud2 Visualization
Shows `/depth_camera/image` and `/depth_camera/points` visualizing the wall behind the robot model from the newly added `depth_camera_link`:

![RViz Depth Camera Display](screenshots/rviz_depth_camera.png)

---

### 2. Step 7: Computation Graph (`rqt_graph`) during `square.launch.py`
Shows active ROS 2 nodes, topics, services, and action client/server connections while the robot executes the autonomous square driving trajectory:

![rqt_graph during square.launch.py](screenshots/rqt_graph_square.png)

---

## Building the Workspace

1. Ensure the ROS 2 environment is sourced (make sure active conda environments are deactivated):
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
  4. In RViz, displays for `/depth_camera/image` and `/depth_camera/points` are pre-configured.

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

## What Did Not Work and Why (Technical Analysis)

1. **Anaconda Python vs ROS 2 Interface Generator (`rosidl_adapter`):**
   - *Problem:* When building `my_robot_interfaces`, `colcon build` initially failed with `ModuleNotFoundError: No module named 'em'`.
   - *Cause:* The active Anaconda base environment in `$PATH` hijacked the Python interpreter during CMake generation, but lacked the ROS 2 IDL dependencies (`empy`).
   - *Solution:* Deactivating Conda (`conda deactivate`) and enforcing the system Python interpreter via `--cmake-args -DPython3_EXECUTABLE=/usr/bin/python3` solved the build conflict.

2. **Heading Angle Discontinuity across $\pm\pi$:**
   - *Problem:* In the `/rotate` action server, subtracting the initial yaw angle from the current yaw angle caused sharp wrap-around jumps when the robot turned past the negative X-axis ($+\pi \to -\pi$).
   - *Cause:* Quaternions converted to Euler yaw are constrained to $[-\pi, \pi]$.
   - *Solution:* Implemented incremental difference integration (`angle_difference(current_yaw, prev_yaw)`), accumulating small delta changes between consecutive `/odom` messages to guarantee monotonic turn tracking.
