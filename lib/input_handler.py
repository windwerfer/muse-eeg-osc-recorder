# Collect events until released
import os
import sys
import time

from lib.record_to_file import gracefully_end
from lib.record_to_file import close_and_zip_files


def start_input(data):

    # user_input = input(" Exit: x (+Enter) | new rec: n | reset nod: n0 \n")  # todo: | note: n | s = stats
    print(" \n to interact with the script press the Command + ENTER (sometimes needs 2 presses :-)")
    print(" Commands: x = Exit | r = rec to file | n0 = reset nod \n")

    time.sleep(3)       # needs to wait shortly (pycharm sends the input to record_to_file.py thread otherwise..)

    while True:



        user_input = input("\r ").encode('utf-8').decode('utf-8', errors='ignore')
       # sys.stdout.flush()      # is that needed??

        if user_input == 'n0':
            data['stats']['moved_continuous'] = 0


        if user_input == 'x':
            gracefully_end(data)


        if user_input == 'r':
            if data['folder']['tmp'] == '':
                print('nothing is recorded right now. returning to normal programm')
            else:
                # print('not yet working.')
                close_and_zip_files(data)


        if user_input == 'n':
            data['stats']['pause'] = True
            note = input(" enter the note to save and press Enter:")
            data['folder']['note'].append( f"{note}" )

            data['stats']['pause'] = False

        if user_input == '':
            print('no command entered.')




       # sys.stdout.write(f"\rYou typed: {user_input}                      \n")
       # sys.stdout.flush()
