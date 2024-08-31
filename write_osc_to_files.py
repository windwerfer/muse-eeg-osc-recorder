
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
from lib.shared_data import Shared_Data
from lib.statistics import start_stats, is_run_in_pycharm

# global config variables init







# Queue object to pass the data streams between files threadsave





def main():

    data = Shared_Data()
    init_conf(data)
    # data['buffer'] = {'eeg': [], 'heart_rate':[], 'acc': [], 'signal_quality': []}
    # data['feedback'] = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
    # data['columns'] = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
    # data['signal'] = {'electrode': [4, 4, 4, 4], 'is_good': 0}
    # data['folder'] = {'out': "out_eeg", 'tmp': ''}
    # data['file'] = {'name': {}, 'open': {}, 'csv_writer': {}}

    stats_thread = threading.Thread(target=start_stats, args=(data), daemon=True)
    stats_thread.start()

    # pycharm has problems with the input.. works great in termux
    if not is_run_in_pycharm():
        input_thread = threading.Thread(target=start_input, args=(data), daemon=True)
        input_thread.start()

    # Starting the separate thread  for writing to file
    write_thread = threading.Thread(target=process_buffers, args=(data))
    write_thread.start()

     # Starting the separate thread  for writing to file
    osc_thread = threading.Thread(target=osc_start, args=(data), daemon=True)
    osc_thread.start()

    # if data['conf']['feedback_acc']:
    #      # Starting the separate thread  for writing to file
    #     feedback_thread = threading.Thread(target=feedback_acc, daemon=True)
    #     feedback_thread.start()

    while True:
        # feedback_acc()
        time.sleep(1)



if __name__ == '__main__':

    main()
