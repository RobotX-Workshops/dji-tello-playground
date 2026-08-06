import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

from joysticks.pygame_connector import PyGameConnector
from joysticks.xbox_controller import XboxPyGameController
from .base_gamepad_adapter import BaseGamepadTelloAdapter
from .utils import run_adapter_test


class XboxTelloControlAdapter(BaseGamepadTelloAdapter):
    def __init__(self, controller: XboxPyGameController) -> None:
        super().__init__(controller)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    controller = XboxPyGameController(pygame_connector)
    tello_control = XboxTelloControlAdapter(controller)
    run_adapter_test(tello_control)
