"""Video file generation functionality.

This module provides functions to generate video files with text content.
It supports multiple video formats and can use either ffmpeg or moviepy as the backend.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from PIL import Image, ImageDraw, ImageFont
    from moviepy.editor import TextClip
    from ..registration import register_generator

PILLOW_AVAILABLE = False
NUMPY_AVAILABLE = False
MOVIEPY_AVAILABLE = False
REGISTRATION_AVAILABLE = False

FreeTypeFont: Any = None
Image: Any = None
ImageDraw: Any = None
ImageFont: Any = None
np: Any = None
TextClip: Any = None
CompositeVideoClip: Any = None
ImageClip: Any = None
register_generator: Any = None

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.ImageFont import FreeTypeFont

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from moviepy.editor import TextClip, CompositeVideoClip, ImageClip

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from ..registration import register_generator

    REGISTRATION_AVAILABLE = True
except ImportError:
    REGISTRATION_AVAILABLE = False


def _create_video_frame(
    text: str,
    width: int = 640,
    height: int = 480,
    bg_color: str = "#000000",
    text_color: str = "#FFFFFF",
    font_size: int = 24,
) -> Any:
    if not PILLOW_AVAILABLE or not NUMPY_AVAILABLE:
        raise ImportError(
            "Video generation requires Pillow and NumPy. "
            "Install with: pip install pillow numpy\n"
            "For additional video format support, install moviepy and ffmpeg:\n"
            "pip install moviepy\n"
            "Note: ffmpeg must be installed separately on your system.\n"
            "See https://ffmpeg.org/ for installation instructions."
        )

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("LiberationSans-Regular.ttf", font_size)
        except (IOError, OSError):
            pass

    if font is not None:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)

        draw.text(position, text, fill=text_color, font=font)

    return image


def _generate_video_with_ffmpeg(text: str, output_path: Path, duration: int = 5, fps: int = 24) -> bool:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            for i in range(duration * fps):
                frame = _create_video_frame(text)
                frame_path = temp_dir_path / f"frame_{i:04d}.png"
                frame.save(frame_path, "PNG")

            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(temp_dir_path / "frame_%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            return True

    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Error generating video with ffmpeg: {e}", file=sys.stderr)
        return False


def _generate_video_with_moviepy(text: str, output_path: Path, duration: int = 5, fps: int = 24) -> bool:
    try:
        print("DEBUG: Creating text clip")
        txt_clip = TextClip(
            text,
            fontsize=70,
            color="white",
            size=(1280, 720),
        )
        print(f"DEBUG: Created text clip: {txt_clip}")

        txt_clip = txt_clip.set_duration(duration)
        print("DEBUG: Set duration on text clip")

        print("DEBUG: Creating background frame")
        frame = _create_video_frame(text)
        print("DEBUG: Created video frame")
        rgb_frame = frame.convert("RGB")
        print("DEBUG: Converted frame to RGB")

        print("DEBUG: Creating image clip")
        color_clip = ImageClip(rgb_frame)
        print(f"DEBUG: Created image clip: {color_clip}")
        color_clip = color_clip.set_duration(duration)
        print("DEBUG: Set duration on image clip")

        print("DEBUG: Creating composite video")
        video = CompositeVideoClip([color_clip, txt_clip])
        print(f"DEBUG: Created composite video: {video}")

        print(f"DEBUG: Writing video to {output_path}")
        write_result = video.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio=False,
        )
        print(f"DEBUG: write_videofile result: {write_result}")

        video.close()
        color_clip.close()
        txt_clip.close()

        return True

    except ImportError as e:
        print(f"MoviePy not available: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(
            f"Error generating video with MoviePy: {e}",
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc()
        return False


def generate_video_file(
    content: str,
    output_path: Union[str, Path],
    duration: int = 5,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
    bg_color: str = "black",
    text_color: str = "white",
    font_size: int = 40,
    use_moviepy: bool = False,
) -> bool:
    if not PILLOW_AVAILABLE or not NUMPY_AVAILABLE:
        raise ImportError("Video generation requires Pillow and NumPy. Install with: pip install pillow numpy")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not use_moviepy and _generate_video_with_ffmpeg(content, output_path, duration, fps):
        return True

    if MOVIEPY_AVAILABLE and _generate_video_with_moviepy(content, output_path, duration, fps):
        return True

    error_msg = (
        "Failed to generate video. Make sure you have either moviepy or ffmpeg "
        "installed.\nInstall with: pip install moviepy numpy pillow\n"
        "Or install ffmpeg: https://ffmpeg.org/download.html\n"
        "Video generation failed. Please check that you have ffmpeg installed "
        "and available in your system PATH."
    )
    raise RuntimeError(error_msg)


def _video_not_available(*args, **kwargs):
    raise ImportError(
        "Video generation requires additional dependencies. "
        "Please install them with:\n"
        "pip install opencv-python numpy pillow moviepy"
    )


try:
    from .registration import register_generator as _register_generator

    register_generator = _register_generator
    REGISTRATION_AVAILABLE = True
except ImportError:
    REGISTRATION_AVAILABLE = False

    def _noop_decorator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    register_generator = _noop_decorator
    print(
        "WARNING: Video generator registration is not available. Required dependencies may be missing.",
        file=sys.stderr,
    )

if register_generator is not None and callable(register_generator):
    if all([PILLOW_AVAILABLE, NUMPY_AVAILABLE, MOVIEPY_AVAILABLE]):
        register_generator(["mp4", "avi", "mov", "mkv"])(generate_video_file)
        print("DEBUG: Successfully registered video generator with formats: mp4, avi, mov, mkv")
    else:
        register_generator(["mp4", "avi", "mov", "mkv"])(_video_not_available)
        print("WARNING: Video generator registered with placeholder. Missing dependencies:")
        if not PILLOW_AVAILABLE:
            print("  - Pillow (PIL)")
        if not NUMPY_AVAILABLE:
            print("  - NumPy")
        if not MOVIEPY_AVAILABLE:
            print("  - MoviePy")
else:
    print(
        "WARNING: Could not register video generator. Required dependencies may be missing.",
        file=sys.stderr,
    )
