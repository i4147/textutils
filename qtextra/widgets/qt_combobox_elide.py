import sys

from qtpy.QtCore import Qt
from qtpy.QtGui import QFontMetrics
from qtpy.QtWidgets import QApplication, QComboBox, QStyle, QStyleOptionComboBox, QStylePainter


class QtElideComboBox(QComboBox):
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)

        text_width = self.width() - 20
        if text_width < 0:
            text_width = 0

        font_metrics = QFontMetrics(self.font())

        elided_text = font_metrics.elidedText(option.currentText, Qt.TextElideMode.ElideRight, text_width)
        option.currentText = elided_text

        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    combo = QtElideComboBox()
    combo.addItems(
        [
            "Short text",
            "This is a very long text that likely needs truncation",
            "Another extremely long text example to demonstrate ellipses…",
        ],
    )
    combo.setEditable(False)
    combo.show()
    sys.exit(app.exec_())
