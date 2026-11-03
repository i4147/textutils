from __future__ import annotations

import typing as ty
from contextlib import contextmanager

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QCloseEvent, QMouseEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

import qtextra.helpers as hp

_W = ty.TypeVar("_W")
_M = ty.TypeVar("_M")


class QListWidgetItemWithModel(QListWidgetItem):
    item_model: _M


class QtListItem(QFrame):
    _evt_checked = Signal(object, bool)

    evt_remove = Signal(object)

    evt_double_clicked = Signal(object, bool)

    evt_active = Signal(object)

    name_label: QLabel

    item: _M | QListWidgetItemWithModel | None = None
    _is_checked: bool = False
    _mode: bool = False

    def _set_from_model(self, _: ty.Any = None) -> None:
        raise NotImplementedError("Must implement method")

    @property
    def item_model(self) -> _M:
        try:
            return self.item.item_model
        except (AttributeError, ValueError):
            return self.item

    @item_model.setter
    def item_model(self, item_model: _M) -> None:
        try:
            self.item.item_model = item_model
        except (AttributeError, ValueError):
            self.item = item_model
        self._set_from_model()

    @property
    def is_checked(self) -> bool:
        return self._is_checked

    @property
    def name(self) -> str:
        return self.name_label.text()

    @property
    def hash_id(self) -> str:
        return self.item_model.name

    @property
    def mode(self) -> bool:
        return self._mode

    @mode.setter
    def mode(self, value: bool) -> None:
        self._mode = bool(value)
        self.setProperty("mode", str(value))
        hp.polish_widget(self)
        self.evt_active.emit(self.item)

    def set_state(self, state: bool) -> None:
        state = bool(state)
        self._is_checked = state
        if hasattr(self, "check_label"):
            self.check_label.setVisible(state)
        elif hasattr(self, "checkbox"):
            with hp.qt_signals_blocked(self.checkbox):
                self.checkbox.setChecked(state)
        self.mode = state
        self._evt_checked.emit(self.item, self._is_checked)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.evt_double_clicked.emit(self.item, self._is_checked)
        super().mouseDoubleClickEvent(event)

    def refresh(self) -> None:
        self._set_from_model()
        parent = self.parentWidget()
        if parent is not None:
            parent.update()

    def _toggle_visibility(self, visible: bool) -> None:
        self.setVisible(visible)
        if not visible:
            self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        else:
            self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.updateGeometry()

        if self.parent() and self.parent().layout():
            self.parent().layout().invalidate()
            self.parent().layout().activate()


class ListMixin:
    _filter_text: str = ""

    def teardown(self) -> None:
        pass

    def refresh_list(self) -> None:
        pass

    @staticmethod
    def _get_search_terms(item_model: _M) -> list[str]:
        return []

    def set_filter_text(self, text: str) -> None:
        self._filter_text = text
        self.apply_filter()

    def apply_filter(self) -> int:
        if not self._filter_text:
            return self.filter_items(lambda _: True)
        needle = self._filter_text.lower()

        def _predicate(widget: _W) -> bool:
            terms = self._get_search_terms(widget.item_model)
            return any(needle in term.lower() for term in terms)

        return self.filter_items(_predicate)

    def filter_items(self, predicate: ty.Callable[[_W], bool]) -> int:
        raise NotImplementedError("Must implement method")

    def filter_by_text(
        self,
        text: str,
        *,
        attr: str = "name",
        case_sensitive: bool = False,
    ) -> int:
        if not text:
            return self.filter_items(lambda _: True)
        needle = text if case_sensitive else text.lower()

        def _predicate(widget: _W) -> bool:
            value = getattr(widget, attr, None)
            if value is None:
                try:
                    value = getattr(widget.item_model, attr, "")
                except Exception:
                    value = ""
            haystack = str(value) if case_sensitive else str(value).lower()
            return needle in haystack

        return self.filter_items(_predicate)

    def all_widget_iter(self) -> ty.Iterator[_W]:
        raise NotImplementedError("Must implement method")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.teardown()
        QWidget.closeEvent(self, event)

    @property
    def n_rows(self) -> int:
        return self.count()

    def get_all_checked(self, *, reverse: bool = False) -> list[int]:
        checked = []
        for index, widget in enumerate(self.widget_iter()):
            if widget.is_checked:
                checked.append(index)
        if reverse:
            return list(reversed(checked))
        return checked

    def get_all_unchecked(self) -> list[int]:
        checked = []
        for index, widget in enumerate(self.widget_iter()):
            if not widget.is_checked:
                checked.append(index)
        return checked

    def get_index_for_hash_id(self, hash_id: str) -> int:
        for index, widget in enumerate(self.all_widget_iter()):
            if widget.hash_id == hash_id:
                return index
        return -1


class QtListWidget(QListWidget, ListMixin):
    evt_updated = Signal(int)
    evt_added = Signal(object)
    evt_pre_remove = Signal(object)
    evt_remove = Signal(object)
    evt_cleared = Signal()

    _is_setup: bool = False

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSpacing(1)
        self.setMinimumHeight(12)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def _get_menu(self) -> None:
        menu = hp.make_menu(self, "Actions")
        menu_remove = hp.make_menu_item(self, "Refresh list...", menu=menu, icon="refresh")
        menu_remove.triggered.connect(self.refresh_list)

    def _get_check_state(self, state: bool, attr: str = "is_checked") -> list[tuple[str, bool]]:
        items: list[tuple[str, bool]] = []
        for widget in self.widget_iter():
            if hasattr(widget, attr) and getattr(widget, attr) == state:
                items.append((widget.hash_id, state))
        return items

    def _check_existing(self, item_model: _M) -> bool:
        return False

    def _make_widget(self, item: QListWidgetItemWithModel) -> _W:
        raise NotImplementedError("Must implement method")

    def widget_iter(self) -> ty.Iterator[_W]:
        for index in range(self.count()):
            item = self.item(index)
            if item is not None and not item.isHidden():
                widget = self.itemWidget(item)
                if widget is not None:
                    yield widget

    def item_iter(
        self,
        indices: ty.Iterable[int] | None = None,
        reverse: bool = False,
    ) -> ty.Iterator[QListWidgetItemWithModel]:
        if indices is None:
            indices = [i for i in range(self.count()) if not self.item(i).isHidden()]

        iterator: ty.Iterable[int]
        iterator = reversed(tuple(indices)) if reverse else tuple(indices)
        for index in iterator:
            item = self.item(index)
            if item is not None:
                yield item

    def item_model_widget_iter(self) -> ty.Iterator[tuple[QListWidgetItemWithModel, _M, _W]]:
        for index in range(self.count()):
            item = self.item(index)
            if item is None or item.isHidden():
                continue
            widget = self.itemWidget(item)
            if widget is not None:
                yield item, item.item_model, widget

    def model_iter(self, indices: ty.Iterable[int] | None = None) -> ty.Iterator[_M]:
        if indices is None:
            indices = [i for i in range(self.count()) if not self.item(i).isHidden()]
        for index in indices:
            item: QListWidgetItemWithModel = self.item(index)
            if item:
                yield item.item_model

    def all_widget_iter(self) -> ty.Iterator[_W]:
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            if widget is not None:
                yield widget

    def all_item_iter(
        self,
        indices: ty.Iterable[int] | None = None,
        reverse: bool = False,
    ) -> ty.Iterator[QListWidgetItemWithModel]:
        if indices is None:
            indices = range(self.count())

        iterator: ty.Iterable[int]
        iterator = reversed(tuple(indices)) if reverse else tuple(indices)
        for index in iterator:
            item = self.item(index)
            if item is not None:
                yield item

    def all_item_model_widget_iter(self) -> ty.Iterator[tuple[QListWidgetItemWithModel, _M, _W]]:
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            if item is not None and widget is not None:
                yield item, item.item_model, widget

    def all_model_iter(self, indices: ty.Iterable[int] | None = None) -> ty.Iterator[_M]:
        if indices is None:
            indices = range(self.count())
        for index in indices:
            item: QListWidgetItemWithModel = self.item(index)
            if item:
                yield item.item_model

    def get_hash_ids(self, indices: ty.Iterable[int]) -> list[str]:
        hash_ids: list[str] = []
        for item_id in indices:
            item = self.item(item_id)
            if item is not None:
                hash_ids.append(item.item_model.name)
        return hash_ids

    def get_attr(self, indices: ty.Iterable[int], attr: str, default: ty.Any = None) -> list[ty.Any]:
        values: list[ty.Any] = []
        for item_id in indices:
            item = self.item(item_id)
            if item is None:
                values.append(default)
                continue
            item_model = item.item_model
            if hasattr(item_model, attr):
                values.append(getattr(item_model, attr))
            elif hasattr(item, attr):
                values.append(getattr(item, attr))
            else:
                values.append(default)
        return values

    def get_item_widget_for_index(self, index: int) -> tuple[QListWidgetItemWithModel, _W]:
        item = self.item(index)
        widget = self.itemWidget(item)
        if item is None or widget is None:
            raise IndexError(f"No list widget item at index {index}")
        return item, widget

    def get_item_model_for_index(self, index: int) -> _M:
        item: QListWidgetItemWithModel = self.item(index)
        return item.item_model

    def get_widget_for_hash_id(self, hash_id: str) -> _W | None:
        index = self.get_index_for_hash_id(hash_id)
        if index == -1:
            return None
        return self.get_item_widget_for_index(index)[1]

    def get_item_for_item_model(self, item_model: _M) -> QListWidgetItem | None:
        for item, _item_model, _ in self.all_item_model_widget_iter():
            if _item_model is item_model or _item_model == item_model:
                return item
        return None

    def get_widget_for_item_model(self, item_model: _M) -> _W | None:
        for _, _item_model, widget in self.all_item_model_widget_iter():
            if _item_model is item_model or _item_model == item_model:
                return widget
        return None

    def get_hash_id_for_index(self, index: int) -> str:
        item = self.get_item_model_for_index(index)
        return item.name

    @Slot(QListWidgetItem)
    @Slot(QListWidgetItem, bool)
    def remove_item(self, item: QListWidgetItemWithModel, force: bool = False) -> None:
        if item is None:
            return
        row = self.row(item)
        if row < 0:
            return

        widget = self.itemWidget(item)
        self.evt_pre_remove.emit(item)
        if widget is not None:
            self.removeItemWidget(item)
        self.takeItem(row)
        if widget is not None:
            widget.deleteLater()
        self.evt_remove.emit(item.item_model)
        self.evt_updated.emit(self.count())

    def remove_by_index(self, index: int, force: bool = False) -> None:
        item = self.item(index)
        if item is not None:
            self.remove_item(item, force)

    def remove_by_item_model(self, item_model: _M, force: bool = False, **_kwargs: ty.Any) -> None:
        item = self.get_item_for_item_model(item_model)
        if item:
            self.remove_item(item, force)

    def move_item(self, index: int, new_index: int, item_model: _M | None = None) -> None:
        if index == new_index:
            return
        item = self.item(index)
        if item is None:
            return
        widget = self.itemWidget(item)
        item = self.takeItem(index)
        self.insertItem(new_index, item)
        if widget is not None:
            self.setItemWidget(item, widget)
        if item_model is not None:
            item.item_model = item_model

    def select_by_index(self, index: int) -> None:
        self.setCurrentRow(index)

    def select_by_item_model(self, item_model: _M) -> None:
        item = self.get_item_for_item_model(item_model)
        if item:
            self.select_by_item(item)

    def select_by_item(self, item: QListWidgetItem) -> None:
        if item is not None:
            self.setCurrentItem(item)

    def refresh(self) -> None:
        for index in range(self.count()):
            widget = self.itemWidget(self.item(index))
            if hasattr(widget, "refresh"):
                widget.refresh()

    def reset_data(self) -> None:
        self.clear()
        self.evt_cleared.emit()

    def append_item(self, item_model: _M) -> tuple[QListWidgetItemWithModel, _W] | tuple[None, None]:
        if self._check_existing(item_model):
            return None, None
        item = QListWidgetItem()
        item.item_model = item_model
        self.addItem(item)
        widget = self._make_widget(item)
        widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        self.evt_added.emit(item_model)
        self.evt_updated.emit(self.count())
        return item, widget

    def insert_item(self, item_model: _M, index: int = 0) -> tuple[QListWidgetItemWithModel, _W] | tuple[None, None]:
        if self._check_existing(item_model):
            return None, None
        item = QListWidgetItem()
        item.item_model = item_model
        self.insertItem(index, item)
        widget = self._make_widget(item)
        widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        self.evt_added.emit(item_model)
        self.evt_updated.emit(self.count())
        return item, widget

    def _clear(self, _: ty.Any) -> None:
        self.clear()
        self.evt_updated.emit(self.count())

    def filter_items(self, predicate: ty.Callable[[_W], bool]) -> int:
        visible = 0
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            if widget is not None:
                show = predicate(widget)
                item.setHidden(not show)
                if show:
                    visible += 1
        return visible

    @contextmanager
    def disable_updates(self) -> ty.Iterator[None]:
        self.setUpdatesEnabled(False)
        try:
            yield
        finally:
            self.setUpdatesEnabled(True)


class QtListScrollWidget(QScrollArea, ListMixin):
    evt_updated = Signal(int)
    evt_added = Signal(object)
    evt_pre_remove = Signal(object)
    evt_remove = Signal(object)
    evt_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.widgets: dict[str, QtListItem] = {}

        scroll_widget = QWidget()
        self.setWidget(scroll_widget)
        self._layout = hp.make_v_layout(parent=scroll_widget, spacing=2, margin=1, stretch_after=True)

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _make_widget(self, item_model: _M) -> _W:
        raise NotImplementedError("Must implement method")

    def count(self) -> int:
        return len(self.widgets)

    @property
    def n_visible(self) -> int:
        return sum(1 for w in self.widgets.values() if not w.isHidden())

    def widget_iter(self) -> ty.Iterator[_W]:
        for widget in self.widgets.values():
            if not widget.isHidden():
                yield widget

    def model_iter(self, indices: ty.Sequence[int] | None = None, reverse: bool = False) -> ty.Iterator[_M]:
        if indices is None:
            widgets = [w for w in self.widgets.values() if not w.isHidden()]
            if reverse:
                widgets.reverse()
            for w in widgets:
                yield w.item_model
        else:
            keys = list(self.widgets.keys())
            selected = [keys[i] for i in indices if i < len(keys)]
            if reverse and selected:
                selected.reverse()
            for key in selected:
                yield self.widgets[key].item_model

    def all_widget_iter(self) -> ty.Iterator[_W]:
        yield from self.widgets.values()

    def all_model_iter(self, indices: ty.Sequence[int] | None = None, reverse: bool = False) -> ty.Iterator[_M]:
        if indices is None:
            indices = range(self.count())
        keys = list(self.widgets.keys())
        selected = [keys[i] for i in indices if i < len(keys)]
        if reverse and selected:
            selected.reverse()
        for key in selected:
            yield self.widgets[key].item_model

    def _check_existing(self, item_model: _M) -> bool:
        raise NotImplementedError("Must implement method")

    def append_item(self, item_model: _M) -> _W | None:
        if self._check_existing(item_model):
            return None
        widget = self._make_widget(item_model)
        widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.widgets = {item_model.unique_id: widget, **self.widgets}
        self._layout.insertWidget(0, widget)
        self.evt_added.emit(item_model)
        self.evt_updated.emit(self.count())
        return widget

    def get_widget_for_item_model(self, item_model: _M) -> _W | None:
        return self.widgets.get(item_model.unique_id)

    def remove_item(self, item_model: _M, force: bool = False) -> None:
        self.evt_pre_remove.emit(item_model)
        widget = self.widgets.get(item_model.unique_id)
        if widget:
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self.widgets.pop(item_model.unique_id, None)
        self.evt_remove.emit(item_model)
        self.evt_updated.emit(self.count())

    def remove_by_item_model(self, item_model: _M, force: bool = False, **_kwargs: ty.Any):
        self.remove_item(item_model, force=force)

    def get_item_widget_for_index(self, index: int) -> tuple[_M, _W]:
        keys = list(self.widgets.keys())
        if index < 0 or index >= len(keys):
            raise IndexError("Index out of range")
        key = keys[index]
        widget = self.widgets[key]
        return widget.item_model, widget

    def get_widget_for_hash_id(self, hash_id: str) -> _W | None:
        index = self.get_index_for_hash_id(hash_id)
        if index == -1:
            return None
        return self.get_item_widget_for_index(index)[1]

    def get_item_for_index(self, index: int) -> _M:
        return self.get_item_widget_for_index(index)[0]

    def get_widget_for_index(self, index: int) -> _W:
        return self.get_item_widget_for_index(index)[1]

    def filter_items(self, predicate: ty.Callable[[_W], bool]) -> int:
        visible = 0
        for widget in self.widgets.values():
            show = predicate(widget)
            widget._toggle_visibility(show)
            if show:
                visible += 1
        return visible

    def reset_data(self) -> None:
        for widget in list(self.widgets.values()):
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self.widgets.clear()
        self.evt_cleared.emit()
        self.evt_updated.emit(0)

    def refresh(self) -> None:
        for widget in self.widgets.values():
            if hasattr(widget, "refresh"):
                widget.refresh()
