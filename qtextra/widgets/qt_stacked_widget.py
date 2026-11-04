from qtpy.QtCore import QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation, pyqtSignal
from qtpy.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


class OpacityAniStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__nextIndex = 0
        self.__effects = []
        self.__anis = []

    def addWidget(self, w: QWidget):
        super().addWidget(w)

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        ani = QPropertyAnimation(effect, b"opacity", self)
        ani.setDuration(220)
        ani.finished.connect(self.__onAniFinished)
        self.__anis.append(ani)
        self.__effects.append(effect)
        w.setGraphicsEffect(effect)

    def setCurrentIndex(self, index: int):
        index_ = self.currentIndex()
        if index == index_:
            return

        if index > index_:
            ani = self.__anis[index]
            ani.setStartValue(0)
            ani.setEndValue(1)
            super().setCurrentIndex(index)
        else:
            ani = self.__anis[index_]
            ani.setStartValue(1)
            ani.setEndValue(0)

        self.widget(index_).show()
        self.__nextIndex = index
        ani.start()

    def setCurrentWidget(self, w: QWidget):
        self.setCurrentIndex(self.indexOf(w))

    def __onAniFinished(self):
        super().setCurrentIndex(self.__nextIndex)


class PopUpAniInfo:
    def __init__(self, widget: QWidget, deltaX: int, deltaY, ani: QPropertyAnimation):
        self.widget = widget
        self.deltaX = deltaX
        self.deltaY = deltaY
        self.ani = ani


class PopUpAniStackedWidget(QStackedWidget):
    aniFinished = pyqtSignal()
    aniStart = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []
        self._nextIndex = None
        self._ani = None

    def addWidget(self, widget, deltaX=0, deltaY=76):
        super().addWidget(widget)

        self.aniInfos.append(
            PopUpAniInfo(
                widget=widget,
                deltaX=deltaX,
                deltaY=deltaY,
                ani=QPropertyAnimation(widget, b"pos"),
            ),
        )

    def removeWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index == -1:
            return

        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setCurrentIndex(
        self,
        index: int,
        needPopOut: bool = False,
        showNextWidgetDirectly: bool = True,
        duration: int = 250,
        easingCurve=QEasingCurve.OutQuad,
    ):
        if index < 0 or index >= self.count():
            raise ValueError(f"The index `{index}` is illegal")

        if index == self.currentIndex():
            return

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        self._nextIndex = index

        nextAniInfo = self.aniInfos[index]
        currentAniInfo = self.aniInfos[self.currentIndex()]

        currentWidget = self.currentWidget()
        nextWidget = nextAniInfo.widget
        ani = currentAniInfo.ani if needPopOut else nextAniInfo.ani
        self._ani = ani

        if needPopOut:
            deltaX, deltaY = currentAniInfo.deltaX, currentAniInfo.deltaY
            pos = currentWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, currentWidget.pos(), pos, duration, easingCurve)
            nextWidget.setVisible(showNextWidgetDirectly)
        else:
            deltaX, deltaY = nextAniInfo.deltaX, nextAniInfo.deltaY
            pos = nextWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, pos, QPoint(nextWidget.x(), 0), duration, easingCurve)
            super().setCurrentIndex(index)

        ani.finished.connect(self.__onAniFinished)
        ani.start()
        self.aniStart.emit()

    def setCurrentWidget(
        self,
        widget,
        needPopOut: bool = False,
        showNextWidgetDirectly: bool = True,
        duration: int = 250,
        easingCurve=QEasingCurve.OutQuad,
    ):
        self.setCurrentIndex(self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __setAnimation(self, ani, startValue, endValue, duration, easingCurve=QEasingCurve.Linear):
        ani.setEasingCurve(easingCurve)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)

    def __onAniFinished(self):
        self._ani.disconnect()
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()
