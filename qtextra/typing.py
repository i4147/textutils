import typing as ty

from koyo.typing import StrEnum

Callback = ty.Union[ty.Callable, ty.Sequence[ty.Callable]]
OptionalCallback = ty.Optional[ty.Union[ty.Callable, ty.Sequence[ty.Callable]]]
Orientation = ty.Literal["horizontal", "vertical"]
IconType = ty.Union[str, tuple[str, dict[str, ty.Any]]]
GifOption = ty.Literal["dots", "infinity", "oval", "circle", "square"]
QtaSizePreset = ty.Literal[
    "xxsmall",
    "xsmall",
    "small",
    "normal",
    "average",
    "medium",
    "large",
    "xlarge",
    "xxlarge",
    "xxxlarge",
    "10px",
    "16px",
    "20px",
    "24px",
    "28px",
    "32px",
    "40px",
    "60px",
    "80px",
    "120px",
]


class TaskState(StrEnum):
    QUEUED = "queued"
    RUN_NEXT = "run-next"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    INCOMPLETE = "incomplete"
    FINISHED = "finished"
    PART_FAILED = "part-failed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    LOCKED = "locked"
    INVALID = "invalid"


class TaskProgress(StrEnum):
    PENDING = "wait"
    COMPLETE = "check"
    INCOMPLETE = "cross"
    ACTIVE = "active"


class WorkerState(StrEnum):
    FINISHED = "finished"
    NOT_ENOUGH_SPACE = "not_enough_space"


class ProcessState(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    CANCEL = "cancel"


class TaskType(StrEnum):
    PROCESS = "process"
    THREAD = "thread"
    CLI = "console"


class State(StrEnum):
    COMPLETE = "check"
    INCOMPLETE = "cross"


class Connectable(ty.Protocol):
    def connect(self, func: ty.Callable) -> ty.Any:
        pass

    def disconnect(self, func: ty.Callable) -> ty.Any:
        pass
