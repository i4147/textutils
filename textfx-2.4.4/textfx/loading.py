import itertools
import random
import sys
import threading
from time import sleep
from termcolor import colored


class SpinnerLoading:
    def __init__(self, message="Loading ", animation="⠋⠙⠸⠴⠦⠇", message_color=None, animation_color=None, delay=0.1):
        self.message = message
        self.animation = animation
        self.message_color = message_color
        self.animation_color = animation_color
        self.delay = delay
        self._done = False
        self._thread = None

    def _animate(self):
        for frame in itertools.cycle(self.animation):
            if self._done:
                break
            sys.stdout.write(f"\r{colored(self.message, self.message_color)}{colored(frame, self.animation_color)}")
            sys.stdout.flush()
            sleep(self.delay)

    def __enter__(self):
        self._done = False
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._done = True
        self._thread.join()


class ProgressBarLoading:
    def __init__(
        self,
        message="Loading",
        barline="-",
        animation="#",
        length=20,
        message_color=None,
        animation_color=None,
        barline_color=None,
        delay=0.1,
    ):
        self.length = length
        self.message = message
        self.animation = animation
        self.message_color = message_color
        self.animation_color = animation_color
        self.barline_color = barline_color
        self.barline = barline
        self.delay = delay
        self._done = False
        self._thread = None
        self._pos = 0
        self._dir = 1

    def _animate(self):
        while not self._done:
            bar = [colored(self.barline, self.barline_color)] * self.length
            bar[self._pos] = colored(self.animation, self.animation_color)
            sys.stdout.write(f"\r{colored(self.message, self.message_color)}: [{''.join(bar)}]")
            sys.stdout.flush()
            sleep(self.delay)
            if self._pos == self.length - 1:
                self._dir = -1
            elif self._pos == 0:
                self._dir = 1
            self._pos += self._dir

    def __enter__(self):
        self._done = False
        self._pos = 0
        self._dir = 1
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._done = True
        self._thread.join()


class GlitchLoading:
    def __init__(self, message="Loading...", delay=0.1, charset="#$%&*@!?", color=None):
        self.message = message
        self.delay = delay
        self.charset = charset
        self.color = color
        self._done = False
        self._thread = None

    def _animate(self):
        while not self._done:
            glitched = "".join(char if random.random() > 0.2 else random.choice(self.charset) for char in self.message)
            sys.stdout.write(f"\r{colored(glitched, self.color)}")
            sys.stdout.flush()
            sleep(self.delay)

    def __enter__(self):
        self._done = False
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._done = True
        self._thread.join()
