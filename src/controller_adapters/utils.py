
import os
import time
from services.tello_controller import TelloController
from joysticks.utils import print_state


def run_adapter_test(contoller: TelloController) -> None:

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        # Test the get_state method
        tello_control_state = contoller.get_state()

        # Print the TelloControlState object
        print("TelloControlState:")
        state_dict = tello_control_state.__dict__
        print_state(state_dict)

        time.sleep(0.1)
