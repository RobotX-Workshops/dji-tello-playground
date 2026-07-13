import logging
import cv2

try:
    from open_cv_wrapper import OpenCvWrapper
except ModuleNotFoundError:
    from face_tracking.open_cv_wrapper import OpenCvWrapper

LOGGER = logging.getLogger(__name__)


class ImageProvider:
    """
    Provides access to the camera and retrieves compressed images.

    Args:
        open_cv (OpenCvWrapper): An instance of the OpenCvWrapper class.
        compression (int, optional): The compression factor for the images. Defaults to 4.
        headless (bool, optional): Specifies whether the program is running in headless mode. Defaults to False.
    """

    def __init__(
        self, open_cv: OpenCvWrapper, compression: int = 4, headless: bool = False
    ):
        """
        Initializes the ImageProvider.

        Args:
            open_cv (OpenCvWrapper): An instance of the OpenCvWrapper class.
            compression (int, optional): The compression factor for the images. Defaults to 4.
            headless (bool, optional): Specifies whether the program is running in headless mode. Defaults to False.
        """
        LOGGER.debug(
            f"Initializing ImageProvider {'in headless mode' if headless else ''} with compression {compression}"
        )
        self.compression = compression
        self.open_cv = open_cv

    def connect_to_camera(self, id: int = 0):
        """
        Connects to the camera with the specified ID.

        Args:
            id (int, optional): The ID of the camera to connect to. Defaults to 0.
        """
        self.cap = self.open_cv.connect_to_camera(id)

    def get_image(self) -> cv2.typing.MatLike:
        """
        Retrieves a compressed image from the connected camera.

        Returns:
            cv2.typing.MatLike: The compressed image.

        Raises:
            Exception: If the camera is not connected.
        """
        if not self.cap.isOpened():
            raise Exception("Camera is not connected")

        compression = self.compression
        _, frame = self.cap.read()
        # Get the image height and width

        compressed_image = self.open_cv.resize(
            frame, (0, 0), fx=1 / compression, fy=1 / compression
        )

        return compressed_image
