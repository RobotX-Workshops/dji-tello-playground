# 🛸 DJI Tello Drone Playground

Welcome to the DJI Tello Drone Playground! This project is designed for enthusiasts and learners who want to explore the capabilities of the DJI Tello drone through a series of practical exercises.

## 🚀 Getting Started

1. [Git clone](https://git-scm.com/docs/git-clone) or download this repository to your computer.
2. [Setup your development environment](./docs/setting_up_the_environment.md).
3. [Connect](#setup-drone-connection) to the drone.
4. Try controlling the drone manually with your smartphone. See [this](./docs/manual_control_with_smartphone.md) guide
5. See the [example exercises](./src/example_exercises) in the [`src`](./src/) folder
6. Try some of the other more advanced exercises in the [`src`](./src/) folder
7. Get creative and make your own scripts
8. Have fun!

## 📡 Setup Drone Connection

To interact with the drone, you must first establish a WiFi connection:

1. Power on your DJI Tello drone.
2. Connect your computer to the drone's WiFi network.

    ![Connecting to Tello WiFi](./docs/images/trello_wifi.png)

    The WiFi network typically appears as `TELLO-XXXXXX`. Default password is usually `12345678`.

## 📂 Folder Structure

The `src` folder contains the core modules and components of the project. Below is an overview of each subfolder and file:

- **[`example_exercises/`](./src/example_exercises/README.md)**  
  Provides sample scripts and exercises that demonstrate how to use the various components of the repository. These examples can serve as learning resources or starting points for new features.

- **[`controller_adapters/`](./src/controller_adapters/README.md)**  
  Contains modules that act as adapters between various input devices (e.g., joysticks, keyboards) and the Tello drone control logic. These adapters standardize control inputs so the drone can interpret commands regardless of the input source. Most files primarily expose classes for use in other scripts, but also include a `__main__` block for standalone manual testing.

- **[`face_tracking/`](./src/face_tracking/README.md)**  
  Includes code for detecting and tracking faces using computer vision techniques. This module may be used for features such as autonomous following or interactive behaviors based on face detection. The files contain classes to be used in other scripts but not executed directly.

- **[`object_detection/`](./src/object_detection/README.md)**  
  Houses functionality related to detecting objects within video feeds. This could be useful for obstacle avoidance, target recognition, or other advanced drone behaviors. Most files can be run directly as standalone demo scripts.

- **[`joysticks/`](./src/joysticks/README.md)**  
  Contains modules for interfacing with different joystick and game controller types. This folder enables the project to support multiple controller configurations for manual drone operation. Most files primarily expose classes for use in other scripts, but also include a `__main__` block for standalone manual testing.

- **[`services/`](./src/services/README.md)**  
  Implements the core services for interacting with the Tello drone, such as establishing connections, sending commands, and managing the drone’s state. The files contain classes to be used in other scripts but not executed directly

## 📝 Exercises

Dive into various [example exercises](./src/example_exercises) located in the `src` folder. Each script guides you through different functionalities of the DJI Tello drone.

To run an exercise, navigate to the [`src`](./src/)  folder and execute the corresponding script:

```bash
python ./<folder>/<script_name>.py
```

Replace <script_name> with the script you wish to run and <folder> with the folder/s the script is located in.

For More info checkout the [README](./src/example_exercises/README.md)

## 🔍 Troubleshooting

- See the drone status indicator states [here](./docs/drone_status_indicator_states.md)
- There are some instances where the drones IMU may need to be calibrated. See the [calibration video guide](https://youtu.be/ne5bofb7J9Y?si=JrDHTRJOB3Kxdrs4)
- The firmware on the Tello drone may need to be updated. See the [firmware update video guide](https://youtu.be/zHYj1hzlH20?si=KWMkrB6HlDayjDrj)
- To position itself, the drone uses a downward-facing camera. Ensure the surface is well-lit and has distinct features for the drone to detect. Poor lighting or a lack of distinct patterns on the floor may cause the drone to drift or lose position.

### Port Already in Use Error

If you encounter an error like `client_socket.bind(("", Tello.CONTROL_UDP_PORT))` when trying to connect to the drone, it means another process is using the Tello UDP port (usually port 8889).

**Solutions:**

1. **Find and kill the process using the port:**
   ```bash
   # Find the process ID (PID) using the port
   lsof -i :8889
   
   # Kill the process (replace <PID> with the actual process ID)
   kill -9 <PID>
   ```

2. **Check for stuck Python processes:**
   ```bash
   # List all Python processes
   ps aux | grep python
   
   # Kill stuck Python processes if found
   killall python3  # ⚠️ WARNING: kills ALL Python 3 processes, not just the one on port 8889 — prefer targeted kill -9 <PID> above
   ```

3. **Restart your computer** if the above doesn't work - this will clear all stuck processes.

4. **Use debug mode** for testing without connecting to the drone:
   ```bash
   DEBUG_MODE=true PYTHONPATH=src python3 ./src/example_exercises/your_script.py
   ```

## 🐞 Debugging with Visual Studio Code

To enhance your coding and debugging experience, we recommend using the launch configurations with Visual Studio Code (VS Code).

## 📚 Other Resources

- [Official Docs](https://dl-cdn.ryzerobotics.com/downloads/tello/20180910/Tello%20SDK%20Documentation%20EN_1.3.pdf)
- [Gamepad Control](https://github.com/cozmobotics/Tello-Swarm-Gamepad)
- [Alternate SDK](https://github.com/ErnGusMik/python-tello/tree/main)
- [Api Repository](https://github.com/honglan3/dji-sdk-DJITelloPy?tab=readme-ov-file)
- [User Manual](https://dl-cdn.ryzerobotics.com/downloads/Tello/20180212/Tello+User+Manual+v1.0_EN_2.12.pdf)
- [Swarm Programming](https://drive.google.com/file/d/1vV73j8Axua5dT8gTwts66TzexJLJBqKR/view)
- [Basic Simulator](https://github.com/Fireline-Science/tello_sim)
- [Advanced Simulator](https://dev.droneblocks.io/simulator.html)
- [YolovV8 Inference Container](https://github.com/anjrew/yolo-v8-inference-container/tree/main?tab=readme-ov-file)
- [Tello Pilots Forum](https://tellopilots.com/)
