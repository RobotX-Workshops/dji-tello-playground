import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

from joysticks.tectinter_controller_windows import TectInterJoystick
from joysticks.pygame_connector import PyGameConnector
from .base_gamepad_adapter import BaseGamepadTelloAdapter
from .utils import run_adapter_test


class TectInterJoystickControlAdapter(BaseGamepadTelloAdapter):
    def __init__(self, controller: TectInterJoystick):
        super().__init__(controller)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    controller = TectInterJoystick(pygame_connector)
    tello_control = TectInterJoystickControlAdapter(controller)
    run_adapter_test(tello_control)
