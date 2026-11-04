import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import cv2

from .base import BaseValidator, ValidationResult

HAS_OPENCV = False
try:
    import cv2

    HAS_OPENCV = True
except ImportError:
    pass

HAS_FFPROBE = bool(
    subprocess.run(
        ["which", "ffprobe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).returncode
    == 0
)


class VideoValidator(BaseValidator):
    FORMAT: Optional[str] = None

    @classmethod
    def validate(cls, file_path: str) -> ValidationResult:
        try:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(is_valid=False, message=f"File not found: {file_path}")

            if not path.is_file():
                return ValidationResult(is_valid=False, message=f"Not a file: {file_path}")

            if cls.FORMAT and not file_path.lower().endswith(f".{cls.FORMAT}"):
                return ValidationResult(
                    is_valid=False,
                    message=(f"Expected .{cls.FORMAT} file, got {Path(file_path).suffix}"),
                )

            if path.stat().st_size == 0:
                return ValidationResult(is_valid=False, message="File is empty")

            if HAS_OPENCV:
                result = cls._validate_with_opencv(file_path)
                if result.is_valid:
                    return result

            if HAS_FFPROBE:
                result = cls._validate_with_ffprobe(file_path)
                if result.is_valid:
                    return result

            return ValidationResult(
                is_valid=False,
                message=("Could not validate video (missing dependencies: install OpenCV or ffmpeg)"),
                details={
                    "opencv_available": HAS_OPENCV,
                    "ffprobe_available": HAS_FFPROBE,
                    "size": path.stat().st_size,
                },
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating video file: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _validate_with_opencv(cls, file_path: str) -> ValidationResult:
        if not HAS_OPENCV:
            return ValidationResult(is_valid=False, message="OpenCV is not available")

        try:
            if not os.access(file_path, os.R_OK):
                return ValidationResult(is_valid=False, message=f"File not readable: {file_path}")

            cap = cv2.VideoCapture(file_path)

            if not cap.isOpened():
                return ValidationResult(is_valid=False, message="Could not open video file with OpenCV")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            ret, frame = cap.read()
            if not ret:
                return ValidationResult(is_valid=False, message="Could not read any frames from the video")

            cap.release()

            return ValidationResult(
                is_valid=True,
                message=(f"Valid video: {width}x{height} @ {fps:.2f} fps, {frame_count} frames"),
                details={
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "frame_count": frame_count,
                    "duration_seconds": duration,
                    "validated_with": "opencv",
                },
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating with OpenCV: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def _validate_with_ffprobe(cls, file_path: str) -> ValidationResult:
        if not HAS_FFPROBE:
            return ValidationResult(is_valid=False, message="ffprobe is not available")

        try:
            result = subprocess.run(
                command=[
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=codec_name,width,height,r_frame_rate,duration,nb_frames",
                    "-show_entries",
                    "format=format_name,duration,size",
                    "-of",
                    "json",
                    file_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            try:
                info = json.loads(result.stdout)
                if not info:
                    return ValidationResult(is_valid=False, message="No video information found")

                if "streams" not in info or not info["streams"]:
                    return ValidationResult(is_valid=False, message="No video streams found")

                format_name = info.get("format", {}).get("format_name", "unknown")
                return ValidationResult(is_valid=True, message=f"Video is valid: {format_name}")

            except json.JSONDecodeError:
                return ValidationResult(is_valid=False, message="Invalid JSON output from ffprobe")

            return ValidationResult(is_valid=False, message="Unknown validation error occurred")

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Error validating with ffprobe: {str(e)}",
                details={"error": str(e)},
            )


class Mp4Validator(VideoValidator):
    FORMAT = "mp4"


class AviValidator(VideoValidator):
    FORMAT = "avi"


class MovValidator(VideoValidator):
    FORMAT = "mov"


class MkvValidator(VideoValidator):
    FORMAT = "mkv"


class WebmValidator(VideoValidator):
    FORMAT = "webm"


class FlvValidator(VideoValidator):
    FORMAT = "flv"


class WmvValidator(VideoValidator):
    FORMAT = "wmv"


class MpegValidator(VideoValidator):
    FORMAT = "mpeg"


class M4vValidator(VideoValidator):
    FORMAT = "m4v"


class ThreeGpValidator(VideoValidator):
    FORMAT = "3gp"


class MtsValidator(VideoValidator):
    FORMAT = "mts"


class M2tsValidator(VideoValidator):
    FORMAT = "m2ts"


class VobValidator(VideoValidator):
    FORMAT = "vob"


class AsfValidator(VideoValidator):
    FORMAT = "asf"


class SwfValidator(VideoValidator):
    FORMAT = "swf"


class MpgValidator(VideoValidator):
    FORMAT = "mpg"


class MpeValidator(VideoValidator):
    FORMAT = "mpe"


class M2vValidator(VideoValidator):
    FORMAT = "m2v"


class TsValidator(VideoValidator):
    FORMAT = "ts"


class MxfValidator(VideoValidator):
    FORMAT = "mxf"


class OggValidator(VideoValidator):
    FORMAT = "ogg"


class OgvValidator(VideoValidator):
    FORMAT = "ogv"


class F4vValidator(VideoValidator):
    FORMAT = "f4v"


class MjpegValidator(VideoValidator):
    FORMAT = "mjpeg"


class Mj2Validator(VideoValidator):
    FORMAT = "mj2"


class DvValidator(VideoValidator):
    FORMAT = "dv"


class H261Validator(VideoValidator):
    FORMAT = "h261"


class H263Validator(VideoValidator):
    FORMAT = "h263"


class H264Validator(VideoValidator):
    FORMAT = "h264"


class H265Validator(VideoValidator):
    FORMAT = "h265"


class HevcValidator(VideoValidator):
    FORMAT = "hevc"


class Vp8Validator(VideoValidator):
    FORMAT = "vp8"


class Vp9Validator(VideoValidator):
    FORMAT = "vp9"


class Av1Validator(VideoValidator):
    FORMAT = "av1"


class TheoraValidator(VideoValidator):
    FORMAT = "ogv"


class ProresValidator(VideoValidator):
    FORMAT = "mov"


class DnxhdValidator(VideoValidator):
    FORMAT = "mxf"


class CineformValidator(VideoValidator):
    FORMAT = "avi"


class AnimationValidator(VideoValidator):
    FORMAT = "mov"


class LagarithValidator(VideoValidator):
    FORMAT = "avi"


class UtVideoValidator(VideoValidator):
    FORMAT = "avi"


class HapValidator(VideoValidator):
    FORMAT = "mov"


class NotchlcValidator(VideoValidator):
    FORMAT = "mov"


class SheervideoValidator(VideoValidator):
    FORMAT = "avi"
