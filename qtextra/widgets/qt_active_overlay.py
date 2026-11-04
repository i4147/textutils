from __future__ import annotations

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QBrush, QPainter, QPen
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget

from qtextra.config import THEMES


class QtActiveOverlay(QWidget):
    timer_id: int | None = None
    counter: int = 0

    REVERSE: bool = False
    N_DOTS: int = 5
    INTERVAL: int = 200
    SIZE = 20
    SPACING = 50

    def __init__(self, n_dots: int = 5, interval: int = 200, size: int = 20, spacing=50, parent=None):
        self.N_DOTS = n_dots
        self.INTERVAL = interval
        self.SIZE = size
        self.SPACING = spacing
        QWidget.__init__(self, parent)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(event.rect(), QBrush(THEMES.get_qt_color("background")))

        painter.setPen(QPen(Qt.PenStyle.NoPen))

        height = (self.height() - self.SIZE) // 2

        total_width = (self.N_DOTS - 1) * self.SPACING + self.SIZE

        horizontal_offset = (self.width() - total_width) // 2

        for i in range(self.N_DOTS):
            if i <= self.counter:
                color = "success" if not self.REVERSE else "primary"
            else:
                color = "primary" if not self.REVERSE else "success"
            painter.setBrush(QBrush(THEMES.get_qt_color(color)))
            x = horizontal_offset + i * self.SPACING
            painter.drawEllipse(x, height, self.SIZE, self.SIZE)

    def showEvent(self, event):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
        self.timer_id = self.startTimer(self.INTERVAL)
        self.counter = 0
        super().showEvent(event)

    def timerEvent(self, event):
        if event.timerId() != self.timer_id:
            return super().timerEvent(event)
        self.counter += 1
        if self.counter >= self.N_DOTS:
            self.REVERSE = not self.REVERSE
            self.counter = 0
        self.update()
        return None

    def hideEvent(self, event):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
            self.timer_id = None
        super().hideEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(self.SPACING * (self.N_DOTS + 1), 120)

    def minimumHeight(self) -> QSize:
        return QSize(self.SPACING * (self.N_DOTS + 1), 120)


class QtActiveWidget(QWidget):
    def __init__(self, text: str = "", which: str = "infinity", size: tuple[int, int] = (64, 64), parent=None):
        super().__init__(parent)

        from qtextra.helpers import make_label, make_loading_gif

        label = make_label(self, text, bold=True)
        spinner, _ = make_loading_gif(self, size=size, which=which)

        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(spinner, alignment=Qt.AlignmentFlag.AlignCenter)


if __name__ == "__main__":

    def _main():
        import sys

        from qtextra.utils.dev import qframe

        app, frame, va = qframe(False)

        va.addWidget(QLabel("QtActiveWidget"), alignment=Qt.AlignmentFlag.AlignHCenter)
        va.addWidget(QtActiveWidget(parent=frame))
        va.addWidget(QLabel("QtActiveOverlay"), alignment=Qt.AlignmentFlag.AlignHCenter)
        va.addWidget(QtActiveOverlay(parent=frame))

        frame.show()
        sys.exit(app.exec_())

    _main()
