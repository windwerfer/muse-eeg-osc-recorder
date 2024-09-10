import sys
import os
import time

if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix-like systems
    import tty
    import termios
    import fcntl


def get_key_pressed():
    if os.name == 'nt':  # Windows
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
        return None
    else:  # Unix-like systems
        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        def set_nonblocking(fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        set_nonblocking(sys.stdin.fileno())

        try:
            char = getch()
            if char:
                return char
        except IOError:
            pass

        return None


# Example usage with CPU usage optimization:
if __name__ == "__main__":
    print("Press any key to see what you pressed, or 'x' to exit.")
    while True:
        key = get_key_pressed()
        if key:
            if key.lower() == 'x':
                print("You pressed 'x'. Exiting.")
                break
            else:
                print(f"You pressed: {key}")
        time.sleep(0.1)  # Add a small delay to reduce CPU usage