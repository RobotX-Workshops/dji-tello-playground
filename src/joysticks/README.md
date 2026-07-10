# Joysticks

This package contains the low-level joystick/game controller integrations used by the [`controller_adapters/`](../controller_adapters/README.md) package to translate raw input into Tello drone commands.

Each supported controller has one or more platform-specific implementations (e.g. `xbox_controller_linux.py`, `xbox_controller_mac.py`, `xbox_controller_windows.py`) behind a common wrapper (e.g. `xbox_controller.py`) that picks the right implementation for the current OS at runtime.

See [Controllers and Joysticks](../../docs/controllers.md) for the list of controllers supported on each platform.

Most files primarily expose classes for use by the `controller_adapters/` package, but also include a `__main__` block so you can run them directly to print the live controller/joystick state for manual testing, for example:

```bash
python xbox_controller.py
```

For a generic joystick (not one of the named controllers above), use `pygame_joystick_tester.py` to inspect its raw axes, buttons, and hats:

```bash
python pygame_joystick_tester.py
```
