
import os
import time
from src.services.tello_controller import TelloController

def print_state(state_dict: dict, indent=""):
    for k, v in state_dict.items():
        if isinstance(v, dict):
            print(f"{indent}{k}:")
            print_state(v, indent + "  ")
        else:
            print(f"{indent}{k}: {v}")



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
