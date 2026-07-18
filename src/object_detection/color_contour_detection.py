"""
Color-based contour detection.

This mirrors the donkeycar line-follower approach: take a frame, convert it to
HSV, threshold a configured color range with ``cv2.inRange`` to build a binary
mask, then pull out contours of that color with ``cv2.findContours``.

The color range lives in a small :class:`ColorContourConfig` dataclass so the
detector is "configured" the same way the donkeycar part is - you point it at a
color (or use one of the presets) and it finds blobs of that color.

OpenCV HSV ranges (8-bit):
    H: 0..179   S: 0..255   V: 0..255

Note on red: red wraps around the hue boundary (both near H=0 and H=179), so a
single (lower, upper) range can't capture it. Set ``lower_hsv2``/``upper_hsv2``
(see the ``red`` preset) and both ranges are OR'd together into the mask.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

try:
    from utils import draw_object_box, get_frame_box_dimensions_delta
except ModuleNotFoundError:
    from object_detection.utils import (
        draw_object_box,
        get_frame_box_dimensions_delta,
    )


HsvBound = Tuple[int, int, int]


@dataclass
class ColorContourConfig:
    """
    Configuration for :class:`ColorContourDetector`.

    Args:
        lower_hsv: Lower HSV bound of the color to detect (H 0..179, S/V 0..255).
        upper_hsv: Upper HSV bound of the color to detect.
        lower_hsv2: Optional second lower bound, used for hue-wrapping colors
            such as red. When set (together with ``upper_hsv2``) a second mask
            is OR'd into the result.
        upper_hsv2: Optional second upper bound (see ``lower_hsv2``).
        min_area: Contours smaller than this pixel area are discarded as noise.
        blur_kernel: Size of the Gaussian blur applied before thresholding to
            reduce speckle. Must be odd; set to 0 or 1 to disable.
        highlight_color: BGR color used when drawing detections.
    """

    lower_hsv: HsvBound
    upper_hsv: HsvBound
    lower_hsv2: Optional[HsvBound] = None
    upper_hsv2: Optional[HsvBound] = None
    min_area: float = 300.0
    blur_kernel: int = 5
    highlight_color: Tuple[int, int, int] = (0, 255, 0)


# A handful of ready-to-use color presets so callers don't have to remember
# HSV ranges. Tune these to your lighting - they are sensible starting points.
COLOR_PRESETS = {
    "red": ColorContourConfig(
        lower_hsv=(0, 120, 70),
        upper_hsv=(10, 255, 255),
        lower_hsv2=(170, 120, 70),
        upper_hsv2=(179, 255, 255),
        highlight_color=(0, 0, 255),
    ),
    "green": ColorContourConfig(
        lower_hsv=(40, 70, 70),
        upper_hsv=(80, 255, 255),
        highlight_color=(0, 255, 0),
    ),
    "blue": ColorContourConfig(
        lower_hsv=(100, 120, 70),
        upper_hsv=(130, 255, 255),
        highlight_color=(255, 0, 0),
    ),
    "yellow": ColorContourConfig(
        lower_hsv=(20, 100, 100),
        upper_hsv=(35, 255, 255),
        highlight_color=(0, 255, 255),
    ),
}


@dataclass
class ColorContour:
    """A single detected blob of the configured color."""

    contour: NDArray[np.int32]
    area: float
    # Axis-aligned bounding box in pixels.
    left: int
    top: int
    right: int
    bottom: int

    @property
    def center(self) -> Tuple[int, int]:
        """(x, y) pixel center of the bounding box."""
        return ((self.left + self.right) // 2, (self.top + self.bottom) // 2)


class ColorContourDetector:
    """
    Detects contours of a configured color in an image.

    Usage:
        detector = ColorContourDetector(COLOR_PRESETS["red"])
        detections = detector.detect(frame_bgr)       # largest-first
        frame = detector.draw(frame_bgr, detections)  # overlay boxes
    """

    def __init__(self, config: ColorContourConfig):
        self.config = config

    def create_mask(self, img_bgr: cv2.typing.MatLike) -> NDArray[np.uint8]:
        """
        Build a binary mask of the configured color from a BGR image.

        Args:
            img_bgr: Input image in BGR format (as returned by OpenCV / the
                Tello frame reader).

        Returns:
            An 8-bit single-channel mask (0 or 255) where the color matched.
        """
        cfg = self.config

        # Optional blur to knock down sensor speckle before thresholding.
        kernel = cfg.blur_kernel
        if kernel and kernel > 1:
            kernel = kernel if kernel % 2 == 1 else kernel + 1
            img_bgr = cv2.GaussianBlur(img_bgr, (kernel, kernel), 0)

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(
            hsv,
            np.asarray(cfg.lower_hsv, dtype=np.uint8),
            np.asarray(cfg.upper_hsv, dtype=np.uint8),
        )

        # Second range for hue-wrapping colors (e.g. red).
        if cfg.lower_hsv2 is not None and cfg.upper_hsv2 is not None:
            mask2 = cv2.inRange(
                hsv,
                np.asarray(cfg.lower_hsv2, dtype=np.uint8),
                np.asarray(cfg.upper_hsv2, dtype=np.uint8),
            )
            mask = cv2.bitwise_or(mask, mask2)

        # Morphological open/close cleans up ragged edges and fills pinholes.
        morph_kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, morph_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)
        return mask

    def detect(self, img_bgr: cv2.typing.MatLike) -> List[ColorContour]:
        """
        Find contours of the configured color, largest first.

        Args:
            img_bgr: Input image in BGR format.

        Returns:
            A list of :class:`ColorContour`, sorted by area descending, with
            contours smaller than ``config.min_area`` filtered out.
        """
        mask = self.create_mask(img_bgr)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detections: List[ColorContour] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.config.min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            detections.append(
                ColorContour(
                    contour=contour,
                    area=area,
                    left=x,
                    top=y,
                    right=x + w,
                    bottom=y + h,
                )
            )

        detections.sort(key=lambda d: d.area, reverse=True)
        return detections

    def detect_largest(
        self, img_bgr: cv2.typing.MatLike
    ) -> Optional[ColorContour]:
        """Return the single biggest color blob, or None if nothing matched."""
        detections = self.detect(img_bgr)
        return detections[0] if detections else None

    def offset_from_center(
        self, img_bgr: cv2.typing.MatLike, detection: ColorContour
    ) -> Tuple[int, int]:
        """
        Vector from the detection's center to the frame center, in pixels.

        Handy for steering the drone: a positive x means the target is left of
        center, positive y means it is above center. See
        :func:`utils.get_frame_box_dimensions_delta`.
        """
        frame_height, frame_width = img_bgr.shape[:2]
        return get_frame_box_dimensions_delta(
            detection.left,
            detection.top,
            detection.right,
            detection.bottom,
            frame_width,
            frame_height,
        )

    def draw(
        self,
        img_bgr: cv2.typing.MatLike,
        detections: List[ColorContour],
        outline_contours: bool = True,
    ) -> cv2.typing.MatLike:
        """
        Overlay detections on the image (bounding box, label, and outline).

        Args:
            img_bgr: The image to draw on (modified in place and returned).
            detections: Detections from :meth:`detect`.
            outline_contours: When True, also trace the raw contour shape.

        Returns:
            The annotated image.
        """
        color = self.config.highlight_color
        for idx, det in enumerate(detections):
            if outline_contours:
                cv2.drawContours(img_bgr, [det.contour], -1, color, 1)
            draw_object_box(
                img_bgr,
                det.left,
                det.top,
                det.right,
                det.bottom,
                f"#{idx} area={int(det.area)}",
                color,
            )
            cx, cy = det.center
            cv2.circle(img_bgr, (cx, cy), 4, color, -1)
        return img_bgr


# Usage example: detect a color in a still image.
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Detect contours of a specific color in an image."
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Path to an image file. Defaults to the bundled circles.jpg.",
    )
    parser.add_argument(
        "--color",
        default="red",
        choices=sorted(COLOR_PRESETS.keys()),
        help="Which color preset to detect (default: red).",
    )
    args = parser.parse_args()

    image_path = args.image
    if image_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "circles.jpg")

    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Could not read image: {image_path}")

    detector = ColorContourDetector(COLOR_PRESETS[args.color])
    found = detector.detect(img)
    print(f"Found {len(found)} '{args.color}' contour(s)")
    detector.draw(img, found)

    cv2.imshow(f"Color Contours ({args.color})", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
