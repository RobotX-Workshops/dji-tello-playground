import logging
from typing import Any
import cv2

LOGGER = logging.getLogger(__name__)


class OpenCvWrapper:

    def connect_to_camera(self, id: int = 0) -> cv2.VideoCapture:
        LOGGER.debug(f"Connecting to camera id {id}")
        return cv2.VideoCapture(id)

    def resize(self, *args, **kwargs: Any) -> cv2.typing.MatLike:
        """
        Resizes an image using keyword arguments.

        :param kwargs: Keyword arguments directly passed to cv2.resize.
        :return: Resized image.
        """
        return cv2.resize(*args, **kwargs)

    def get_face_classifier(self) -> cv2.CascadeClassifier:
        return cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    def convert_rgb_image_to_gray(
        self, image: cv2.typing.MatLike
    ) -> cv2.typing.MatLike:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def show_image(self, window_name: str, image: cv2.typing.MatLike) -> None:
        cv2.imshow(window_name, image)

    def listen_for_key(self, delay: int = 1) -> int:
        return cv2.waitKey(delay)

    def rectangle(self, *args, **kwargs) -> cv2.typing.MatLike:
        return cv2.rectangle(*args, **kwargs)

    def write_text(self, *args, **kwargs) -> cv2.typing.MatLike:
        return cv2.putText(*args, **kwargs)
