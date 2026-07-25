# Controller Adapters

This package contains adapters that adapt the output from a gamepad or other controller to the input expected by the Tello Controller (`TelloControlState`, defined in [`services/`](../services/README.md)).

See the "Adapter" in this image for a visual representation of the Adapter pattern:

![Adapter](../../docs/images/architechture.svg)

## Files

- `gc102_controller_tello_adapter.py`, `keyboard_controller.py`, `logitech_f710_tello_adapter.py`, `tectinter_tello_adapter.py`, `xbox_controller_tello_adapter.py`, `xbox_one_tello_adapter.py` — one adapter per supported input device (see [Controllers and Joysticks](../../docs/controllers.md)). Each has a `__main__` block that calls the shared `utils.run_adapter_test()` helper, so you can run any of them directly to manually test its output, e.g. `python xbox_controller_tello_adapter.py`.
- `follow_face_controller.py` — `FaceFollowingController`, a different kind of adapter that converts a face-tracking movement vector (not joystick/gamepad input) into a `TelloControlState`. Used by `example_exercises/follow_face.py` and `mock_follow_face.py`.
- `utils.py` — shared `run_adapter_test()` manual-test loop used by the adapter scripts above; not a standalone script.
