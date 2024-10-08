

import threading

import os
import time


from lib.feedback import feedback_acc_start
from lib.init_config import init_conf
from lib.input_handler import start_input
from lib.osc_server import osc_start
from lib.record_to_file import process_buffers, gracefully_end
from lib.shared_data import Shared_Data
from lib.statistics import start_stats, is_run_in_pycharm
from lib.web_server import start_web_server
from lib.util import create_folder


def main():

    data = Shared_Data()
    init_conf(data)

    server_folder = data['conf']['graphs_folder']
    create_folder(server_folder)
    web_server_thread = threading.Thread(target=start_web_server, args=(server_folder,), daemon=True)
    web_server_thread.start()

    stats_thread = threading.Thread(target=start_stats, args=(data,), daemon=True)
    stats_thread.start()

    # pycharm has problems with the input.. works great in termux
    #if not is_run_in_pycharm():
    # if False:
    input_thread = threading.Thread(target=start_input, args=(data,), daemon=True)
    input_thread.start()

    # Starting the separate thread  for writing to file
    write_thread = threading.Thread(target=process_buffers, args=(data,))
    write_thread.start()

     # Starting the separate thread  for writing to file
    osc_thread = threading.Thread(target=osc_start, args=(data,), daemon=True)
    osc_thread.start()

    # if data['conf']['feedback_acc']:
    #      # Starting the separate thread  for writing to file
    #     feedback_thread = threading.Thread(target=feedback_acc_start, args=(data,), daemon=True)
    #     feedback_thread.start()

    try:
        while True:
            feedback_acc_start(data)
            time.sleep(0.2)
    except KeyboardInterrupt:
        gracefully_end(data)


    finally:
        pass




if __name__ == '__main__':

    main()
