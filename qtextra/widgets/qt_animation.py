import os.path
from contextlib import contextmanager
from enum import auto

from napari.utils.misc import StringEnum
from qtpy.QtCore import QObject, QTimer, Signal, Slot


class LoopMode(StringEnum):
    ONCE = auto()
    LOOP = auto()
    BACK_AND_FORTH = auto()


LOOP_COUNTS = {
    LoopMode.ONCE: 1,
    LoopMode.LOOP: 1,
    LoopMode.BACK_AND_FORTH: 2,
}
LOOP_MODE_TRANSLATIONS = {LoopMode.ONCE: "Once", LoopMode.LOOP: "Loop", LoopMode.BACK_AND_FORTH: "Back-and-forth"}


class QtAnimationBase(QObject):
    evt_lock = Signal(bool)
    evt_started = Signal()
    evt_finished = Signal()
    evt_reset = Signal()
    evt_active = Signal(bool)
    evt_next_requested = Signal(int)

    evt_writer_setup = Signal()
    evt_writer_updated = Signal(int, int)
    evt_writer_finished = Signal()

    def __init__(self, parent, fps):
        QObject.__init__(self, parent)
        self.timer = QTimer(self)

        self._stop: bool = False
        self.is_running: bool = False
        self.interval: int = 0
        self.step: int = 1
        self.current, self.min_point, self.max_point = 0, None, None
        self.loop_mode = str(LoopMode.ONCE)
        self.dim_range = (0, 0, 1)

        self._writer = None
        self._writer_n_loops: int = 1
        self._writer_current_iter: int = 0
        self._writer_max_iter: int = 0
        self._writer_finished: bool = False
        self._writer_current_step: int = 0
        self._writer_max_step: int = 0

    def reset(self):
        self.is_running: bool = False
        self.interval: int = 0
        self.step: int = 1
        self.current, self.min_point, self.max_point = 0, None, None
        self.loop_mode = str(LoopMode.ONCE)
        self.dim_range = (0, 0, 1)

        self._writer = None
        self._writer_n_loops: int = 1
        self._writer_current_iter: int = 0
        self._writer_max_iter: int = 0
        self._writer_finished: bool = False
        self._writer_current_step: int = 0
        self._writer_max_step: int = 0

    def setup(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def update(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def _animate(self, current: int):
        pass

    @property
    def writer(self):
        return self._writer

    @property
    def writer_max_iter(self) -> int:
        return self._writer_max_iter

    @writer_max_iter.setter
    def writer_max_iter(self, value):
        self._writer_max_iter = value
        self._writer_current_iter = value
        self._writer_current_step = 0
        self._writer_max_step = value * self.max_point

    def set_writer(
        self,
        filename: str,
        fps: int = 10,
        loop: int = 0,
        duration: float = 0.1,
        n_loops: int = 1,
        quality: int = 5,
        **kwargs,
    ):
        import imageio

        if n_loops < 1:
            raise ValueError("The `n_loops` value must be larger than 1.")
        if fps < 1:
            raise ValueError("The `fps` value must be larger than 1.")

        if self._writer is not None:
            self.close_writer()

        if filename.endswith(".gif"):
            self._writer = imageio.get_writer(filename, mode="I", duration=duration, fps=fps, loop=loop)
        elif os.path.splitext(filename)[-1] in [".mov", ".avi", ".mpg", ".mpeg", ".mp4", ".mkv", ".wmv"]:
            self._writer = imageio.get_writer(filename, mode="I", fps=fps, quality=quality)
        self._writer_n_loops = n_loops
        self.writer_max_iter = LOOP_COUNTS[self.loop_mode] * n_loops
        self._writer_finished = False
        self.set_writer_extras(**kwargs)
        self.evt_writer_setup.emit()

    def set_writer_extras(self, **kwargs):
        pass

    def close_writer(self):
        if self._writer:
            self._writer.close()
            self._writer = None
            self._writer_current_iter = 0

    @Slot(float)
    def set_fps(self, fps: float):
        if fps == 0:
            return self.finish()
        self.step = 1 if fps > 0 else -1
        self.interval = 1000 / abs(fps)
        return None

    @Slot(str)
    def set_loop_mode(self, mode: str):
        self.loop_mode = LoopMode(mode)

    def start(self):
        self._stop, self.is_running = False, True
        self.evt_active.emit(True)
        self.timer.singleShot(int(self.interval), self.advance)

    @contextmanager
    def pause(self):
        if not self.is_running:
            raise ValueError("Cannot pause timer that is not running")
        self.timer.stop()
        yield
        self.timer.singleShot(int(self.interval), self.advance)

    def restart(self):
        self.finish()
        self.start()

    def finish(self):
        self._stop, self.is_running = True, False
        self.timer.stop()
        self.evt_active.emit(False)
        self.evt_finished.emit()

        if self._writer and self._writer_current_iter == 0:
            self._writer_finished = True
            self.evt_writer_finished.emit()

    def advance(self):
        if self._stop:
            return None

        self.current += self.step * self.dim_range[2]
        if self.current < self.min_point:
            self._writer_current_iter -= 1
            if self.loop_mode == LoopMode.BACK_AND_FORTH:
                self.step *= -1
                self.current = self.min_point + self.step * self.dim_range[2]
            elif self.loop_mode == LoopMode.LOOP:
                self.current = self.max_point + self.current - self.min_point
            else:
                return self.finish()
        elif self.current >= self.max_point:
            self._writer_current_iter -= 1
            if self.loop_mode == LoopMode.BACK_AND_FORTH:
                self.step *= -1
                self.current = self.max_point + 2 * self.step * self.dim_range[2]
            elif self.loop_mode == LoopMode.LOOP:
                self.current = self.min_point + self.current - self.max_point
            else:
                return self.finish()

        self.evt_next_requested.emit(self.current)
        self.timer.singleShot(int(self.interval), self.advance)
        return None
