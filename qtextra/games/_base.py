from __future__ import annotations

from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

import qtextra.helpers as hp
from qtextra.config.theme import THEMES


class GameBoardWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state: object = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_state(self, state: object) -> None:
        self._state = state
        self.update()

    def _game_over_overlay(self, alpha: int = 70) -> QColor:
        color = QColor(THEMES.get_hex_color("error"))
        color.setAlpha(alpha)
        return color


class GameDialogMixin:
    def _create_board_widget(self) -> GameBoardWidget:
        raise NotImplementedError

    def _instructions_text(self) -> str:
        raise NotImplementedError

    def _do_restart(self) -> None:
        raise NotImplementedError

    def _do_advance_state(self) -> None:
        raise NotImplementedError

    def _score_text(self) -> str:
        return f"Score: {self._state.score}"

    def _game_over_status(self) -> str:
        return "Game over"

    def _is_terminal_state(self) -> bool:
        return self._state.is_game_over

    def _status_text(self) -> str:
        if self._is_terminal_state():
            return self._game_over_status()
        if self._is_paused:
            return "Paused"
        return "Running"

    def _setup_extra_header_widgets(self, header_layout: QHBoxLayout) -> None:
        pass

    def _refresh_extra_labels(self) -> None:
        pass

    def _setup_game_timer(self, interval_ms: int) -> None:
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.advance_game)

    def make_panel(self) -> QVBoxLayout:
        self.score_label = hp.make_label(
            self,
            "",
            bold=True,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        self.status_label = hp.make_label(
            self,
            "",
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.score_label)
        self._setup_extra_header_widgets(header_layout)
        header_layout.addStretch(1)
        header_layout.addWidget(self.status_label)

        self.board_widget = self._create_board_widget()
        self.instructions_label = hp.make_label(
            self,
            self._instructions_text(),
            wrap=True,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        self.pause_button = hp.make_btn(self, "Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.restart_button = hp.make_btn(self, "Restart")
        self.restart_button.clicked.connect(self.restart_game)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.restart_button)

        layout = hp.make_v_layout()
        layout.addLayout(header_layout)
        layout.addWidget(self.board_widget, stretch=1)
        layout.addWidget(self.instructions_label)
        layout.addLayout(button_layout)
        return layout

    def closeEvent(self, event: object) -> None:
        self.timer.stop()
        super().closeEvent(event)

    def restart_game(self) -> None:
        self._do_restart()
        self._is_paused = False
        self.timer.start()
        self._refresh_ui()
        self.setFocus()

    def toggle_pause(self) -> None:
        if self._is_terminal_state():
            self.setFocus()
            return
        self._is_paused = not self._is_paused
        if self._is_paused:
            self.timer.stop()
        else:
            self.timer.start()
        self._refresh_ui()
        self.setFocus()

    def advance_game(self) -> None:
        if self._is_paused or self._is_terminal_state():
            return
        self._do_advance_state()
        if self._is_terminal_state():
            self.timer.stop()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        self.score_label.setText(self._score_text())
        self._refresh_extra_labels()
        self.status_label.setText(self._status_text())
        self.pause_button.setText("Resume" if self._is_paused else "Pause")
        self.board_widget.set_state(self._state)
