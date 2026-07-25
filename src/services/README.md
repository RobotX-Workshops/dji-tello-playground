# Services Module

The `services` module provides the core functionality for interacting with the DJI Tello drone:

- `TelloConnector` — wraps `djitellopy.Tello`; handles the connection lifecycle, movement primitives, and telemetry (battery, height, flight time, attitude, etc.).
- `TelloCommandDispatcher` — translates a `TelloControlState` into RC control calls and discrete actions (takeoff/land/emergency-stop/flips).
- `TelloController` (abstract base), `TelloControlState`, and `TelloActionType` — the control-interface contract that other modules (e.g. `controller_adapters/`) implement against.
- `FrontEnd` — orchestrates the connection/dispatch/control loop and displays live video via `cv2.imshow`.
- `TelloTV` — a minimal stub that currently just holds a `TelloConnector` reference.

Files expose classes to be used by other scripts (e.g. `example_exercises/`, `controller_adapters/`) and are not executed directly — none of the files in this folder define a `__main__` block.
