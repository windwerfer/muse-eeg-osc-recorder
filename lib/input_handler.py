# Collect events until released
import os
import sys

from lib.record_to_file import gracefully_end


def start_input(data):
    # time.sleep(2)
    while True:
        user_input = input("  --> Exit: x (+Enter)  \n")  # todo: | note: n | s = stats
        sys.stdout.flush()

        if user_input == 'x':
            gracefully_end(data)
            os._exit(0)

        sys.stdout.write(f"\rYou typed: {user_input}                      \n")
        sys.stdout.flush()