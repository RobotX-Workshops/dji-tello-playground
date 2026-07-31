"""This script is a simple example of how to use the keyboard as a joystick.

This script will print the joystick actions when a key is pressed or released.

It will open a window with a black background that must be focused for the keyboard commands to be logged to the console

Press 'q' to quit the game."""

import pygame


def main() -> None:
    # Initialize Pygame
    pygame.init()

    pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Keyboard as Joystick")

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                print(f"Joystick action: {event}")
            elif event.type == pygame.KEYUP:
                print(f"Joystick action released: {event}")

    # Quit the game
    pygame.quit()


if __name__ == "__main__":
    main()
