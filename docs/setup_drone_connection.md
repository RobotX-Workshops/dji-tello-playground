## Setup Drone Connection

To interact with the drone, you must first establish a WiFi connection:

1. Power on your DJI Tello drone by quickly pressing and releasing the main power button.
2. Look at the aircraft status lights. It should go though the following sequence:
   - Alternating red, green, and yellow: The drone is turning on and performing self diagnostic tests.
   - Yellow blinking quickly: Before you've connected, this means the drone is ready to connect to a WiFi network (the same blink pattern means something different once connected — see the [status indicator reference](./drone_status_indicator_states.md)).
   - The drone will only stay in the waiting state for a short while. Try restarting the drone if it becomes unreachable by turning it on and off again.
3. Connect your computer to the drone's WiFi network.

    ![Connecting to Tello WiFi](./images/trello_wifi.png)

    The WiFi network typically appears as `TELLO-XXXXXX`. Default password is usually `12345678`.
    