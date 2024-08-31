# Collect events until released
import os
import sys



def start_input(data):
    # time.sleep(2)
    while True:
        user_input = input("  --> Exit: x (+Enter) | note: n | s = stats       \n")
        sys.stdout.flush()

        if user_input == 'x':
            #gracefully_end()
            os._exit(0)

        sys.stdout.write(f"\rYou typed: {user_input}                      \n")
        sys.stdout.flush()