import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

from joysticks.gc102_controller import GC102PyGameController
from joysticks.pygame_connector import PyGameConnector
from .base_gamepad_adapter import BaseGamepadTelloAdapter
from .utils import run_adapter_test


class GC102TelloControlAdapter(BaseGamepadTelloAdapter):
    def __init__(self, controller: GC102PyGameController):
        super().__init__(controller)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    controller = GC102PyGameController(pygame_connector)
    tello_control = GC102TelloControlAdapter(controller)
    run_adapter_test(tello_control)
