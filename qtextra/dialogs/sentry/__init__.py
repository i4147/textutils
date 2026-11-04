from __future__ import annotations

import typing as ty
from contextlib import suppress
from pathlib import Path

import sentry_sdk
from qtpy.QtWidgets import QWidget

INSTALLED = False


__all__ = [
    "FeedbackDialog",
    "TelemetryOptInDialog",
    "ask_opt_in",
    "capture_exception",
    "get_sample_event",
    "install_error_monitor",
]

capture_exception = sentry_sdk.capture_exception


def __getattr__(name: str):
    if name == "FeedbackDialog":
        from qtextra.dialogs.sentry.feedback import FeedbackDialog

        return FeedbackDialog
    if name == "TelemetryOptInDialog":
        from qtextra.dialogs.sentry.telemetry import TelemetryOptInDialog

        return TelemetryOptInDialog
    if name == "get_sample_event":
        from qtextra.dialogs.sentry.utilities import get_sample_event

        return get_sample_event
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Settings(ty.Protocol):
    telemetry_enabled: bool
    telemetry_with_locals: bool


def ask_opt_in(settings: Settings, force: bool = False, parent: QWidget | None = None) -> Settings:
    assert settings is not None, "Settings must be provided."

    enabled_attr = "enabled" if hasattr(settings, "enabled") else "telemetry_enabled"
    with_locals_attr = "with_locals" if hasattr(settings, "with_locals") else "telemetry_with_locals"

    assert hasattr(settings, enabled_attr), f"Settings must have '{enabled_attr}' attribute."
    assert hasattr(settings, with_locals_attr), f"Settings must have '{with_locals_attr}' attribute."

    if not force and getattr(settings, enabled_attr) is not None:
        return settings

    from qtextra.dialogs.sentry.telemetry import TelemetryOptInDialog

    dlg = TelemetryOptInDialog(parent=parent, with_locals=getattr(settings, with_locals_attr))
    send: bool | None = None
    if bool(dlg.exec()):
        send = True
    elif dlg._no:
        send = False

    if send is not None:
        setattr(settings, enabled_attr, send)
        setattr(settings, with_locals_attr, dlg._send_locals)
    return settings


def install_error_monitor(settings: Settings, **extra_kws: ty.Any) -> None:
    global INSTALLED
    if INSTALLED:
        return

    enabled_attr = "enabled" if hasattr(settings, "enabled") else "telemetry_enabled"
    with_locals_attr = "with_locals" if hasattr(settings, "with_locals") else "telemetry_with_locals"

    settings = ask_opt_in(settings)
    if not getattr(settings, enabled_attr):
        return

    from qtextra.dialogs.sentry.utilities import configure_scope_tags, configure_user, get_sentry_settings

    _settings = get_sentry_settings()
    _settings["include_local_variables"] = getattr(settings, with_locals_attr)
    sentry_sdk.init(**_settings)
    configure_user()
    configure_scope_tags()
    if extra_kws:
        set_extra_tags(**extra_kws)
    INSTALLED = True


def set_extra_tags(**kwargs: ty.Any) -> None:
    for k, v in kwargs.items():
        sentry_sdk.set_tag(k, v)


def report_memory_usage() -> str:
    import tempfile

    import psutil
    from koyo.faulthandler import submit_sentry_attachment
    from koyo.utilities import human_readable_byte_size

    tmp = Path(tempfile.gettempdir())
    path = tmp / "memory_usage.txt"
    memory_text = f"Total memory: {human_readable_byte_size(psutil.virtual_memory().total)}\n"
    memory_text += f"Available memory: {human_readable_byte_size(psutil.virtual_memory().available)}\n"
    with suppress(Exception):
        process = psutil.Process()
        pid = process.pid
        mem = process.memory_info()

        memory_text += f"RMS ({pid}): {human_readable_byte_size(mem.rss)}\n"
        memory_text += f"VMS ({pid}): {human_readable_byte_size(mem.rss)}\n"
    path.write_text(memory_text)
    submit_sentry_attachment("Current memory usage - encountered memory issues", path)
    with suppress(Exception):
        path.unlink()
    return memory_text
