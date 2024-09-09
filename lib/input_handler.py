# Collect events until released
import os
import sys

from lib.record_to_file import gracefully_end
from lib.record_to_file import close_and_zip_files


def start_input(data):
    # time.sleep(2)
    # user_input = input(" Exit: x (+Enter) | new rec: n | reset nod: n0 \n")  # todo: | note: n | s = stats

    while True:

        start_input = input(" to interact with the script press ENTER \n")  # todo: | note: n | s = stats
        sys.stdout.flush()

        if start_input == '':
            data['stats']['pause'] = True
            user_input = input(" options:  Exit: x (+Enter) | new rec: n | reset nod: n0 \n")

            if user_input == 'n0':
                data['stats']['moved_continuous'] = 0
                data['stats']['pause'] = False

            if user_input == 'x':
                gracefully_end(data)
                os._exit(0)

            if user_input == 'n':
                close_and_zip_files(data)
                data['stats']['pause'] = False

        #
        # if user_input == 'n':
        #     close_and_zip_files(data)
        #
        # if user_input == 'n0':
        #     data['stats']['moved_continuous'] = 0
        #
        # if user_input == 'x':
        #     gracefully_end(data)
        #     os._exit(0)

       # sys.stdout.write(f"\rYou typed: {user_input}                      \n")
       # sys.stdout.flush()
