
import os
import sys
import threading

from queue import Queue




import psutil
import zipfile
from typing import Dict, List

import csv
import time
from datetime import datetime
import math
import argparse

from lib.init_config import init_conf
from lib.input_handler import start_input
from lib.osc_server import osc_start
from lib.record_to_file import process_buffers, gracefully_end
from lib.statistics import start_stats, is_run_in_pycharm

# global config variables init
global conf
conf = {}



global signal
signal = {}
signal['electrode'] = [4, 4, 4, 4]
signal['is_good'] = 0  # start with 0

global columns
columns = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}

# Queue object to pass the data streams between files threadsave
buffered_data = {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'signal_quality': Queue()}
buffered_feedback = {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'signal_quality': Queue()}



def main():

    conf = init_conf()

    #keyboard.on_press(on_press)    #needs root on android


    stats_thread = threading.Thread(target=start_stats, args=(conf), daemon=True)
    stats_thread.start()

    # pycharm has problems with the input.. works great in termux
    if not is_run_in_pycharm():
        input_thread = threading.Thread(target=start_input, daemon=True)
        input_thread.start()

    # Starting the separate thread  for writing to file
    write_thread = threading.Thread(target=process_buffers, args=(conf))
    write_thread.start()

     # Starting the separate thread  for writing to file
    osc_thread = threading.Thread(target=osc_start, args=(conf), daemon=True)
    osc_thread.start()

    # if conf['feedback_acc']:
    #      # Starting the separate thread  for writing to file
    #     feedback_thread = threading.Thread(target=feedback_acc, daemon=True)
    #     feedback_thread.start()

    while True:
        # feedback_acc()
        time.sleep(1)



if __name__ == '__main__':

    main()
