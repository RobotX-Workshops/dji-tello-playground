# Object Detection Module

This module implements basic object detection algorithms. It provides functionalities for detecting circular objects and edges in images using computer vision techniques.

## Color contour detection

`color_contour_detection.py` finds contours of a **specific color**, configured
the same way the donkeycar line-follower is: pick a color range (or a preset)
and it thresholds the image in HSV with `cv2.inRange` and pulls out the matching
blobs with `cv2.findContours`.

```python
from object_detection.color_contour_detection import (
    ColorContourDetector,
    ColorContourConfig,
    COLOR_PRESETS,
)

# Use a preset...
detector = ColorContourDetector(COLOR_PRESETS["red"])

# ...or configure your own HSV range (H 0..179, S/V 0..255):
detector = ColorContourDetector(
    ColorContourConfig(lower_hsv=(40, 70, 70), upper_hsv=(80, 255, 255))
)

detections = detector.detect(frame_bgr)   # largest blob first
if detections:
    largest = detections[0]
    print(largest.center, largest.area)
    dx, dy = detector.offset_from_center(frame_bgr, largest)  # for steering
frame_bgr = detector.draw(frame_bgr, detections)             # overlay boxes
```

Presets: `red` (handles hue wrap-around), `green`, `blue`, `yellow`. Tune the
HSV ranges to your lighting.

Try it on an image:

```bash
python src/object_detection/color_contour_detection.py path/to/image.jpg --color green
```

For a **live drone demo** with HSV tuning sliders that steers the Tello to keep
the largest color blob centered, see
`src/example_exercises/16_color_contour_detector.py`.
