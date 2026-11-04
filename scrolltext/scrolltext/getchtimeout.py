import select
import sys
import termios
import tty


class GetchWithTimeout:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)

    def getch(self, timeout: float = 0.15):
        input_array = [sys.stdin]
        ready_tuple = select.select(input_array, [], [], timeout)
        if len(ready_tuple[0]) > 0:
            return ready_tuple[0][0].read(1)
        return None

    def cleanup(self):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        print()
