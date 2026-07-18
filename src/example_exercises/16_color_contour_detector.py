"""
Live color-contour detection on the Tello video stream.

Detects contours of a specific color (configured via HSV trackbars), draws them
on the frame, and steers the drone to keep the largest blob centered - the
color-tracking analogue of the circle detector in ``15_circle_dectector.py``.

The heavy lifting lives in ``object_detection.color_contour_detection``; this
script just wires that detector to the drone stream (or a local webcam in
DEBUG_MODE) and adds HSV tuning sliders.

Controls:
    q / ESC   quit and land
    Trackbars tune the HSV color range live

Modes (edit the flags below):
    DEBUG_MODE  = True   use a local webcam, no drone at all
    NO_TAKEOFF  = True   use the drone camera but keep it on the ground
"""

import os
import signal
import sys
import time
from typing import Optional

import cv2
from djitellopy import Tello

# Make the object_detection package importable when run directly.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
from object_detection.color_contour_detection import (  # noqa: E402
    COLOR_PRESETS,
    ColorContourConfig,
    ColorContourDetector,
)

# Set to True to use the local webcam for debugging, False to use the drone.
DEBUG_MODE = False
# Set to True to use the drone camera but not take off (test detection safely).
NO_TAKEOFF = True

# Which preset to seed the trackbars with on startup.
START_COLOR = "red"

# Control parameters.
FORWARD_SPEED = 15  # cm/s forward speed once the target is centered
YAW_SENSITIVITY = 0.1  # px offset -> yaw velocity
UP_DOWN_SENSITIVITY = 0.2  # px offset -> up/down velocity
CENTER_TOLERANCE = 40  # px: within this of center counts as "centered"
MIN_TRACK_AREA = 500  # ignore blobs smaller than this for navigation

# Global handles for the signal handler.
tello: Optional[Tello] = None
cap: Optional[cv2.VideoCapture] = None


def emergency_landing(signum=None, frame=None):
    """Land and clean up on Ctrl+C / termination."""
    print("\n⚠️  Emergency shutdown triggered!")
    if tello is not None and not DEBUG_MODE:
        try:
            print("Sending emergency land command...")
            tello.send_rc_control(0, 0, 0, 0)
            tello.land()
            tello.end()
            print("✓ Drone landed safely")
        except Exception as e:
            print(f"Error during emergency landing: {e}")
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Cleanup complete. Exiting...")
    sys.exit(0)


signal.signal(signal.SIGINT, emergency_landing)
signal.signal(signal.SIGTERM, emergency_landing)


def resolve_video_source(cli_value: Optional[str]) -> str:
    """Resolve the active video source from CLI or environment."""
    env_value = os.getenv("VIDEO_SOURCE")
    if cli_value:
        return cli_value
    if env_value:
        return env_value
    return "0"


def open_capture(source: str) -> cv2.VideoCapture:
    """Create a cv2.VideoCapture from either a device index or a URL."""
    if source.isdigit():
        return cv2.VideoCapture(int(source))
    return cv2.VideoCapture(source)


WINDOW = "Color Contour Detection"


def _noop(_):
    pass


def build_trackbars(preset: ColorContourConfig) -> None:
    """Create HSV range sliders seeded from a preset."""
    cv2.namedWindow(WINDOW)
    lo_h, lo_s, lo_v = preset.lower_hsv
    hi_h, hi_s, hi_v = preset.upper_hsv
    cv2.createTrackbar("H min", WINDOW, lo_h, 179, _noop)
    cv2.createTrackbar("H max", WINDOW, hi_h, 179, _noop)
    cv2.createTrackbar("S min", WINDOW, lo_s, 255, _noop)
    cv2.createTrackbar("S max", WINDOW, hi_s, 255, _noop)
    cv2.createTrackbar("V min", WINDOW, lo_v, 255, _noop)
    cv2.createTrackbar("V max", WINDOW, hi_v, 255, _noop)
    cv2.createTrackbar("min area", WINDOW, int(preset.min_area), 5000, _noop)


def read_config_from_trackbars() -> ColorContourConfig:
    """Build a detector config from the current slider positions."""
    return ColorContourConfig(
        lower_hsv=(
            cv2.getTrackbarPos("H min", WINDOW),
            cv2.getTrackbarPos("S min", WINDOW),
            cv2.getTrackbarPos("V min", WINDOW),
        ),
        upper_hsv=(
            cv2.getTrackbarPos("H max", WINDOW),
            cv2.getTrackbarPos("S max", WINDOW),
            cv2.getTrackbarPos("V max", WINDOW),
        ),
        min_area=float(cv2.getTrackbarPos("min area", WINDOW)),
        highlight_color=(0, 255, 0),
    )


# --- Set up the drone / camera -------------------------------------------------
if DEBUG_MODE:
    print("Running in DEBUG mode with local camera")
    video_source = resolve_video_source(None)
    cap = open_capture(video_source)
    print(f"Opened camera: {video_source}")
else:
    tello = Tello()
    print("Attempting to connect to drone ...")
    tello.connect()
    print(f"Battery: {tello.get_battery()}%")
    print("Starting camera stream ...")
    tello.streamon()
    print("Waiting for camera to stabilize...")
    time.sleep(2)

build_trackbars(COLOR_PRESETS[START_COLOR])
detector = ColorContourDetector(COLOR_PRESETS[START_COLOR])

if not DEBUG_MODE and not NO_TAKEOFF:
    print("Taking off...")
    tello.takeoff()
    time.sleep(2)
elif not DEBUG_MODE:
    print("NO_TAKEOFF mode - drone will stay on the ground")


# --- Main loop -----------------------------------------------------------------
while True:
    if DEBUG_MODE:
        ret, img = cap.read()
        if not ret or img is None:
            continue
    else:
        img = tello.get_frame_read().frame
        if img is None:
            continue
        # The Tello stream is RGB; convert to BGR for OpenCV color handling.
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    height, width = img.shape[:2]
    frame_center_x = width // 2
    frame_center_y = height // 2

    # Re-read the color config each frame so the sliders apply live.
    detector.config = read_config_from_trackbars()
    detections = detector.detect(img)

    # Draw the frame-center crosshair.
    cv2.line(img, (frame_center_x - 20, frame_center_y),
             (frame_center_x + 20, frame_center_y), (255, 255, 255), 2)
    cv2.line(img, (frame_center_x, frame_center_y - 20),
             (frame_center_x, frame_center_y + 20), (255, 255, 255), 2)

    detector.draw(img, detections)

    yaw_velocity = 0
    forward_velocity = 0
    up_down_velocity = 0

    largest = detections[0] if detections else None
    if largest is not None and largest.area >= MIN_TRACK_AREA:
        # Vector from target center to frame center (positive x = target left).
        offset_x, offset_y = detector.offset_from_center(img, largest)

        # Steer toward the target: turn/rise to reduce the offset.
        yaw_velocity = int(-offset_x * YAW_SENSITIVITY)
        up_down_velocity = int(offset_y * UP_DOWN_SENSITIVITY)
        yaw_velocity = max(-100, min(100, yaw_velocity))
        up_down_velocity = max(-100, min(100, up_down_velocity))

        # Creep forward once roughly centered horizontally.
        if abs(offset_x) < CENTER_TOLERANCE:
            forward_velocity = FORWARD_SPEED

        cv2.line(img, (frame_center_x, frame_center_y),
                 largest.center, (255, 0, 255), 2)
        cv2.putText(img, f"Offset: ({offset_x}, {offset_y})", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Yaw:{yaw_velocity} Fwd:{forward_velocity} "
                    f"UpDn:{up_down_velocity}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    else:
        cv2.putText(img, "No target detected", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Status banner.
    if DEBUG_MODE:
        mode_text = "DEBUG MODE"
    elif NO_TAKEOFF:
        mode_text = "NO TAKEOFF"
    else:
        mode_text = "DRONE FLYING"
    cv2.putText(img, mode_text, (width - 200, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(img, f"Blobs: {len(detections)}", (width - 200, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Only send flight commands when actually airborne.
    if not DEBUG_MODE and not NO_TAKEOFF:
        tello.send_rc_control(0, forward_velocity, up_down_velocity, yaw_velocity)

    cv2.imshow(WINDOW, img)
    time.sleep(1 / 15)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        break

print("\nShutting down...")
emergency_landing()
