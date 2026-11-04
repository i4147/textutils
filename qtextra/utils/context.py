import signal
import socket
from contextlib import contextmanager

from qtpy.QtCore import QSocketNotifier


@contextmanager
def _maybe_allow_interrupt(qapp):
    old_sigint_handler = signal.getsignal(signal.SIGINT)
    handler_args = None
    if old_sigint_handler in (None, signal.SIG_IGN, signal.SIG_DFL):
        yield
        return

    wsock, rsock = socket.socketpair()
    wsock.setblocking(False)
    old_wakeup_fd = signal.set_wakeup_fd(wsock.fileno())
    sn = QSocketNotifier(rsock.fileno(), QSocketNotifier.Type.Read)

    def _drain_signal_socket(*_args) -> None:
        rsock.recv(1)

    sn.activated.connect(_drain_signal_socket)

    def handle(*args):
        nonlocal handler_args
        handler_args = args
        qapp.exit()

    signal.signal(signal.SIGINT, handle)
    try:
        yield
    finally:
        wsock.close()
        rsock.close()
        sn.setEnabled(False)
        signal.set_wakeup_fd(old_wakeup_fd)
        signal.signal(signal.SIGINT, old_sigint_handler)
        if handler_args is not None:
            old_sigint_handler(*handler_args)
