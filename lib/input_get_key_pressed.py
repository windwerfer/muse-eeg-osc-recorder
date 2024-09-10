
import sys
import os

if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix-like systems
    import tty
    import termios
    import fcntl


def get_key_pressed():
    if os.name == 'nt':  # Windows
        # On Windows, we'll simulate key press detection by checking if any key is pressed
        # This isn't as straightforward as on Unix-like systems because keyboard.is_pressed()
        # requires specifying a key. However, we can use a workaround:
        if msvcrt.kbhit():  # Check if a key press is available
            return msvcrt.getch().decode('utf-8')  # Return the key pressed
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
            if char:  # If any key was pressed
                return char
        except IOError:  # No input available
            pass

        return None


# Example usage:
if __name__ == "__main__":
    print("Press any key to see what you pressed, or 'x' to exit.")
    while True:
        key = get_key_pressed()
        if key:
            if key == 'x':
                print("You pressed 'x'. Exiting.")
                break
            else:
                print(f"You pressed: {key}")