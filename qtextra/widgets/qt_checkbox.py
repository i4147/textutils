from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox


class QtTriCheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        QCheckBox.__init__(self, *args, **kwargs)
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        state = self.checkState()
        new_state = Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked
        self.setCheckState(new_state)
