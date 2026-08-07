# Drone Status Indicator States

The table below lists the drone status indicator's colors and patterns and what each one means.

| Category | Color | Pattern | Aircraft State |
| --- | --- | --- | --- |
| Normal States | Alternating red, green, and yellow | Blinking | Turning on and performing self-diagnostic tests |
| Normal States | Green | Periodically blinks twice | Vision Positioning System active |
| Normal States | Yellow | Blinking slowly | Vision Positioning System unavailable, aircraft is in Attitude mode |
| Charging States | Blue | Solid | Charging is complete |
| Charging States | Blue | Blinking slowly | Charging |
| Charging States | Blue | Blinking quickly | Charging error |
| Warning States | Yellow | Blinking quickly | Remote control signal lost |
| Warning States | Red | Blinking slowly | Low battery |
| Warning States | Red | Blinking quickly | Critically low battery |
| Warning States | Red | Solid | Critical error |

![Drone status indicator states](./images/status_indicator_states.png)

> **Note:** "Yellow, blinking quickly" is context-dependent. Before you've connected to the drone's WiFi, this pattern instead means the drone is powered on and ready to pair (see the [connection guide](./setup_drone_connection.md)); the "Remote control signal lost" meaning above applies once you're already connected and flying.
