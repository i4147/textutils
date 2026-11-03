from __future__ import annotations

import atexit
import typing as ty
from contextlib import suppress

from loguru import logger
from qtpy.QtCore import QObject, QProcess, Signal

from qtextra.queue.cli_qprocess import QProcessWrapper
from qtextra.queue.task import Task
from qtextra.typing import Callback, TaskState
from qtextra.utils.utilities import running_under_pytest

logger = logger.bind(src="Queue")


class CLIQueueHandler(QObject):
    CAN_FORCE_START = True

    _evt_cancel = Signal(Task)
    _evt_pause = Signal(Task, bool)

    evt_queued = Signal(Task)

    evt_started = Signal(Task)

    evt_next = Signal(Task)

    evt_finished = Signal(Task)

    evt_empty = Signal()

    evt_cancelled = Signal(Task)

    evt_errored = Signal(Task, object)
    evt_part_errored = Signal(Task, object)

    evt_paused = Signal(Task, bool)

    evt_progress = Signal(Task)

    evt_queue_closed = Signal()

    evt_finished_all = Signal()

    evt_remove_task = Signal(str)

    def __init__(self, parent: QObject | None = None, n_parallel: int = 1, auto_run: bool = True):
        super().__init__(parent=parent)
        self.auto_run = auto_run
        self.n_parallel = n_parallel

        self.queue_closed: bool = False

        self.active_tasks: dict[str, QProcessWrapper] = {}

        self.pending_queue: list[str] = []

        self.running_queue: list[str] = []

        self.finished_queue: list[str] = []
        self._evt_cancel.connect(self._kill)

        self.actions: list[dict] = []

        atexit.register(self.close)

    def add_action(self, title: str, func: ty.Callable[[Task], None], icon: str | None = None) -> None:
        self.actions.append({"title": title, "icon": icon, "func": func})
        logger.trace(f"Added action '{title}'.")

    def has_actions(self) -> bool:
        return len(self.actions) > 0

    def set_max_parallel(self, n_parallel: int) -> None:
        self.n_parallel = n_parallel
        self.run_queued()

    @property
    def n_tasks(self) -> tuple[int, int]:
        return len(self.running_queue), len(self.pending_queue)

    def task_started(self, task: Task) -> None:
        task_id = task.task_id
        if task_id in self.pending_queue:
            self.pending_queue.remove(task_id)

        if task_id not in self.running_queue:
            self.running_queue.append(task_id)
        worker_obj = self.active_tasks.get(task_id)
        if worker_obj:
            logger.trace(f"Task '{worker_obj.summary()}' started.")
        self.evt_started.emit(task)
        self.run_queued()

    def task_finished(self, task: Task) -> None:
        task_id = task.task_id
        worker_obj = self.active_tasks.pop(task_id, None)
        if worker_obj:
            logger.trace(f"Removed '{task_id}' from active tasks (finished).")
            with suppress(ValueError):
                self.running_queue.remove(task_id)
            logger.trace(f"Task '{worker_obj.summary()}' ended.")
        else:
            logger.trace(f"Failed to remove '{task_id}' from active tasks (finished).")
        self.finished_queue.append(task_id)
        self.evt_finished.emit(task)
        self.run_queued()

    def task_cancelled(self, task: Task) -> None:
        task_id = task.task_id
        worker_obj = self.active_tasks.pop(task_id, None)
        if worker_obj:
            logger.trace(f"Removed '{task_id}' from active tasks (cancelled).")

            if worker_obj.is_running():
                self.running_queue.remove(task_id)
            else:
                with suppress(ValueError):
                    self.pending_queue.remove(task_id)
            logger.trace(f"Task '{worker_obj.summary()}' was cancelled.")
        else:
            logger.trace(f"Failed to remove '{task_id}' from active tasks (cancelled).")
        self.finished_queue.append(task_id)
        self.evt_cancelled.emit(task)
        self.run_queued()

    def task_errored(self, task: Task) -> None:
        task_id = task.task_id
        worker_obj = self.active_tasks.pop(task_id, None)
        with suppress(ValueError):
            self.running_queue.remove(task_id)
            logger.trace(f"Removed '{task_id}' from running tasks (errored).")
        with suppress(ValueError):
            self.pending_queue.remove(task_id)
            logger.trace(f"Removed '{task_id}' from pending tasks (errored).")
        if worker_obj:
            logger.trace(f"Removed '{task_id}' from active tasks (errored).")
            logger.trace(f"Task '{worker_obj.summary()}' encountered an error")
            error_info = worker_obj.process.readAllStandardOutput().data().decode()
            self.evt_errored.emit(task, error_info)
        else:
            logger.warning(f"Failed to remove task '{task_id}' from active tasks (errored).")
        self.finished_queue.append(task_id)
        self.run_queued()

    def task_part_errored(self, task: Task) -> None:
        task_id = task.task_id
        worker_obj = self.active_tasks.get(task_id, None)
        if worker_obj:
            logger.trace(f"Task '{worker_obj.summary()}' encountered an error")
            error_info = worker_obj.process.readAllStandardOutput().data().decode()
            self.evt_part_errored.emit(task, error_info)

    def _on_finished(self, task_id: str, error_code: int) -> None:
        if error_code == 0:
            with suppress(KeyError):
                worker_obj = self.active_tasks[task_id]
                self.task_finished(worker_obj.task)
        else:
            with suppress(KeyError):
                worker_obj = self.active_tasks[task_id]
                self.task_errored(worker_obj.task)

    def _on_error_change(self, task_id: str, state: QProcess.ProcessError) -> None:
        if state == QProcess.ProcessError.FailedToStart:
            logger.error("Task failed to start")
        self._on_finished(task_id, -1)

    def _kill(self, task: Task) -> None:
        try:
            worker_obj = self.active_tasks[task.task_id]
            worker_obj.cancel()
        except KeyError:
            logger.warning(f"Failed to cancel '{task.task_id}'")

    def add_complete_task(self, task: Task) -> None:
        if task.state != TaskState.FINISHED:
            raise ValueError(f"Task '{task.summary()}' is not finished.")
        self.evt_queued.emit(task)

    def add_task(
        self,
        task: Task,
        func_error: Callback | None = None,
        func_start: Callback | None = None,
        func_end: Callback | None = None,
        func_post: Callback | None = None,
        add_delayed: bool = True,
        emit_queued: bool = True,
    ) -> str | None:
        if self.queue_closed:
            self.evt_queue_closed.emit()
            return None
        if task.task_id in self.active_tasks:
            logger.warning(f"Task '{task.summary()}' is already in the queue.")
            return None

        worker_obj = self.make_process(
            task=task,
            func_error=func_error,
            func_start=func_start,
            func_end=func_end,
            func_post=func_post,
        )
        self.add_worker(worker_obj, add_delayed=add_delayed, emit_queued=emit_queued)
        return task.task_id

    def add_worker(self, worker_obj: QProcessWrapper, add_delayed: bool = True, emit_queued: bool = True) -> None:
        if not isinstance(worker_obj, QProcessWrapper):
            raise TypeError("You can only add 'QProcessWrapper' objects to the queue")
        logger.trace(f"Added task='{worker_obj.task_id}' to the queue (queue size {self.count()})")

        task_id = worker_obj.task_id
        self.active_tasks[task_id] = worker_obj
        if task_id not in self.pending_queue:
            self.pending_queue.append(task_id)
        if emit_queued:
            self.evt_queued.emit(worker_obj.task)

        if running_under_pytest():
            worker_obj.run()
            logger.trace(f"Running task '{worker_obj.task_id}' in pytest environment")
        else:
            if add_delayed or not self.is_available():
                logger.trace("Added task to queue without running it.")
                return
            worker_obj.run()
            logger.trace(f"Running task '{worker_obj.task_id}' immediately.")

    def make_process(
        self,
        task: Task,
        func_error: Callback | None = None,
        func_start: Callback | None = None,
        func_end: Callback | None = None,
        func_post: Callback | None = None,
    ) -> QProcessWrapper:
        worker_obj = QProcessWrapper(self, task, func_start, func_error, func_end, func_post)
        worker_obj.evt_started.connect(self.task_started)
        worker_obj.evt_finished.connect(self.task_finished)
        worker_obj.evt_next.connect(self.evt_next.emit)
        worker_obj.evt_errored.connect(self.task_errored)
        worker_obj.evt_part_errored.connect(self.task_part_errored)
        worker_obj.evt_progress.connect(self.evt_progress.emit)
        worker_obj.evt_paused.connect(self.evt_paused.emit)
        worker_obj.evt_cancelled.connect(self.task_cancelled)
        return worker_obj

    def run_queued(self) -> None:
        if self.queue_closed and len(self.running_queue) == 0:
            self.evt_finished_all.emit()
            return

        if self.auto_run and self.is_available() and self.pending_queue:
            task_id = self.pending_queue.pop(0)
            worker_obj = self.active_tasks[task_id]
            worker_obj.run()

        if not self.pending_queue and not self.running_queue:
            self.evt_empty.emit()

    def run_force(self, task: Task) -> None:
        try:
            logger.trace(f"Manually starting '{task.summary()}'")
            task_id = task.task_id
            worker_obj = self.active_tasks[task_id]
            try:
                worker_obj.run()
            except Exception as e:
                logger.exception(f"Could not forcefully start specified task - '{task.summary()}'")
                self.evt_errored.emit(task, e)
        except (IndexError, KeyError, AttributeError):
            logger.exception(f"Could not forcefully start specified task - '{task.summary()}'")

    @staticmethod
    def can_cancel(_task: Task) -> ty.Tuple[bool, bool]:
        return True, True

    @staticmethod
    def can_pause(_task: Task) -> bool:
        return False

    def requeue(self, task: Task, remove: bool = False) -> None:
        if remove:
            self.remove(task)
        if task.task_id in self.active_tasks:
            logger.trace(f"Task '{task.summary()}' is already in the active tasks.")
            self.evt_queued.emit(task)
            return
        if task.task_id in self.pending_queue:
            logger.trace(f"Task '{task.summary()}' is already in the pending queue.")
            return
        self.add_task(task)

    def check_if_in_active(self, task: Task) -> bool:
        return task.task_id in self.active_tasks

    def check(self, task: Task) -> None:
        if task.task_id in self.active_tasks:
            logger.trace(f"Task '{task.summary()}' is in the active tasks.")
            return
        self.add_task(task, emit_queued=False)
        logger.trace(f"Task '{task.summary()}' is not in the queue.")

    def remove(self, task: str | Task) -> None:
        task_id = task if isinstance(task, str) else task.task_id
        if task_id in self.active_tasks:
            self.active_tasks.pop(task_id)
            logger.trace(f"Removed '{task_id}' from active tasks (removed).")
        if task_id in self.pending_queue:
            self.pending_queue.remove(task_id)
            logger.trace(f"Removed '{task_id}' from pending tasks (removed).")

    def cancel(self, task: Task) -> None:
        self._evt_cancel.emit(task)

    def pause(self, task: Task, state: bool) -> None:
        try:
            worker_obj = self.active_tasks[task.task_id]
            worker_obj.pause(state)
        except KeyError:
            logger.warning(f"Failed to pause '{task.task_id}'")
        self._evt_pause.emit(task, state)

    def clear(self) -> None:
        to_remove = [*self.pending_queue]
        for task_id in self.active_tasks:
            if task_id not in to_remove and task_id not in self.running_queue:
                to_remove.append(task_id)

        for task_id in to_remove:
            worker_obj = self.active_tasks.pop(task_id, None)
            if worker_obj:
                task = worker_obj.task
                logger.debug(f"Cancelled task '{task.summary()}'")
                with suppress(RuntimeError):
                    self._evt_cancel.emit(task)
        if self.pending_queue:
            self.pending_queue.clear()
            logger.trace("Queue > Cleared queue")
        self.finished_queue.clear()

    def count(self) -> int:
        return len(self.pending_queue)

    def close(self) -> None:
        self.queue_closed = True

        self.clear()

    def is_running(self) -> bool:
        return len(self.running_queue) > 0

    def is_available(self) -> bool:
        return len(self.running_queue) < self.n_parallel

    def is_queued(self, task_id: str) -> bool:
        return task_id in self.pending_queue or task_id in self.running_queue

    def is_finished(self, task_id: str) -> bool:
        return task_id in self.finished_queue

    def remove_task(self, task_id: str) -> None:

        def _remove_if_many(queue: list[str]) -> None:
            while task_id in queue:
                queue.remove(task_id)

        _remove_if_many(self.pending_queue)
        _remove_if_many(self.running_queue)
        _remove_if_many(self.finished_queue)
        with suppress(KeyError):
            worker_obj = self.active_tasks.pop(task_id)
            worker_obj.cancel()
            logger.trace(f"Removed '{task_id}' from active tasks (removed).")
        self.evt_remove_task.emit(task_id)

    def __repr__(self) -> str:
        n_running, n_queued = self.n_tasks
        return f"Queue<queued={n_queued}; running={n_running}>"
