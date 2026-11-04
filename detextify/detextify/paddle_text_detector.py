from detextify.text_detector import TextBox, TextDetector
from paddleocr import PaddleOCR
from typing import Sequence
from PIL import Image

import logging

paddle_logger = logging.getLogger("ppocr").setLevel(logging.ERROR)


class PaddleTextDetector(TextDetector):
    def __init__(self, pad_size: int = 30):
        self.ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, lang="en")
        self.pad_size = pad_size

    def detect_text(self, image_path: str) -> Sequence[TextBox]:
        result = self.ocr.ocr(image_path, cls=True)[0]
        text_boxes = []
        for line in result:
            points = line[0]
            text = line[1][0]
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            tl_x = min(xs)
            tl_y = min(ys)
            h = max(xs) - tl_x
            w = max(ys) - tl_y

            if h < 0 or w < 0:
                logger.error(f"Malformed bounding box from Paddle: {points}")

            if self.pad_size:
                tl_x = max(0, tl_x - self.pad_size)
                tl_y = max(0, tl_y - self.pad_size)

                image = Image.open(image_path)
                max_h = image.height - tl_x
                h = min(h + self.pad_size, image.height - tl_x)
                w = min(w + self.pad_size, image.width - tl_y)

            text_boxes.append(TextBox(int(tl_x), int(tl_y), int(h), int(w), text))
        return text_boxes
