import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

from src.joysticks.logitech_f710_controller import LogitechF710Joystick
from joysticks.pygame_connector import PyGameConnector
from .base_gamepad_adapter import BaseGamepadTelloAdapter
from .utils import run_adapter_test


class LogitechF710ControlAdapter(BaseGamepadTelloAdapter):
    def __init__(self, controller: LogitechF710Joystick):
        super().__init__(controller)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    controller = LogitechF710Joystick(pygame_connector)
    tello_control = LogitechF710ControlAdapter(controller)
    run_adapter_test(tello_control)
