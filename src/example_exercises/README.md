# Example Exercises

This folder contains a collection of sample scripts and exercises designed to help you get started with and understand the functionality of the DJI Tello playground. These examples demonstrate how to use various components of the project—from basic drone commands to more advanced features like computer vision integrations.

Run scripts from the repository root with `src` on your `PYTHONPATH`, since several exercises import sibling packages such as `services`, `face_tracking`, and `controller_adapters`:

```bash
# macOS/Linux
PYTHONPATH=src python3 ./src/example_exercises/<script_name>.py
```

```bat
:: Windows Command Prompt
set PYTHONPATH=src && python ./src/example_exercises/<script_name>.py
```

```powershell
# Windows PowerShell
$env:PYTHONPATH = "src"; python ./src/example_exercises/<script_name>.py
```

Just `cd`-ing into `src` and running a script directly is not enough — scripts like `2_simple_takeoff_land.py` will fail with `ModuleNotFoundError: No module named 'services'` without `PYTHONPATH` set.

The numbered exercises are ordered from basic to advanced concepts, increasing in complexity as they go. Feel free to explore and modify the scripts to suit your needs or experiment with new ideas.

The other scripts (`control_via_gamepad.py`, `follow_face.py`, `mock_follow_face.py`, `navigate_route.py`) demonstrate additional capabilities: manual gamepad/keyboard control, face tracking/following (with a `mock_follow_face.py` webcam-only variant for testing without a drone), and a starting point for autonomous route navigation. Object/circle detection is covered by the numbered exercise `15_circle_dectector.py`, which also supports a `DEBUG_MODE` environment variable to test against a local webcam instead of the drone. It also has a `NO_TAKEOFF` constant (edit the source to set it to `True`) to connect and stream from the drone without taking off.
