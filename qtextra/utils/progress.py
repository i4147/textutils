from __future__ import annotations

import typing as ty

from tqdm import tqdm

try:
    from napari.utils.events.event import EmitterGroup, Event
except ImportError:
    raise ImportError("please install napari using 'pip install napari'") from None


class Progress(tqdm):
    monitor_interval = 0

    def __init__(
        self,
        iterable: ty.Iterable | None = None,
        desc: str | None = None,
        total: int | None = None,
        bar_format: str = "|{bar}| {n_fmt}/{total_fmt} [ETA: {remaining}/{elapsed} {rate_fmt}]",
        *args: ty.Any,
        **kwargs: ty.Any,
    ) -> None:
        self.events = EmitterGroup(value=Event, description=Event, overflow=Event, eta=Event, close=Event)
        self.is_init = True
        super().__init__(iterable, *args, desc=desc, total=total, bar_format=bar_format, **kwargs)

        if not self.desc:
            self.set_description("")
        self.is_init = False

    def __repr__(self) -> str:
        return self.desc

    def display(self, msg: str | None = None, pos: int | None = None) -> None:
        if not self.gui and not self.is_init:
            super().display(msg, pos)
            return
        etas = ""
        if self.total != 0:
            etas = str(self).split("|")[-1]
        self.events.eta(value=etas)

    def update(self, n: float | None = None) -> None:
        super().update(n)
        self.events.value(value=self.n)

    def increment_with_overflow(self) -> None:
        if self.n == self.total:
            self.total = 0
            self.events.overflow()
        else:
            self.update(1)

    def set_description(self, desc: str) -> None:
        super().set_description(desc, refresh=True)
        self.events.description(value=desc)

    def close(self) -> None:
        if self.disable:
            return
        self.events.close()
        self.events.disconnect()
        super().close()
