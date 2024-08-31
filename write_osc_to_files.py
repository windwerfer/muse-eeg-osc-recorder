
import os
import sys
import threading

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import psutil
import zipfile
from typing import Dict, List

import csv
import time
from datetime import datetime
import math
import argparse

# global config variables init
conf = {}
columns = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
folder = {'out' : "out_eeg", 'tmp': ''}
file = {'name':{}, 'open':{}, 'csv_writer': {} }

debug_print = False

# global vaiables that the threads will save there data in
# Bluetooth 4.2
buffered_data = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
buffered_feedback = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}

start_time = None
last_timestamp = {'eeg': 0, 'heart_rate': 0, 'acc': 0, 'signal_quality': 0}
sampling_rate = {'eeg': 256, 'heart_rate': 64,
                 'acc': 52}  # muse s and muse 2 have the same specs for eeg, ppg (heart_rate), and acc (gryoscope)

signal = {}
signal['electrode'] = [4, 4, 4, 4]
signal['is_good'] = 0  # start with 0

stats = {'refresh_interval':0.5, 'cpu': 0, 'cpu_one_core': 0.0, 'nr_cpu_cores': 1, 'battery': None, 'recording': 0, 'counter': '-'}


# format eeglab: only the values, nothing else, no header.. just 4 columns with numbers
# edit->channel location: choose 'import file and erase all channels' (ignore drop down menue) and load the file 'muse_channels.sfp' with the following values (no # and no leading spaces):
#             TP9   -80.0   -50.0   0.0
#             AF7   -70.0   70.0   0.0
#             AF8    70.0   70.0   0.0
#             TP10   80.0   -50.0   0.0
# todo: add a channel_location file to the zip file if packed for eeglab

def terminal_move_up_line_and_clear():
    sys.stdout.write('\033[1A')
    sys.stdout.write('\033[2K')

def is_debugging_with_pycharm():
    """ checks if pycharm started this script through debugger or run mode (sets the env variable) """
    return 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ
def is_run_in_pycharm():
    """ checks if pycharm started this script through debugger or run mode (sets the env variable) """
    return 'PYCHARM_HOSTED' in os.environ

def get_process_cpu_usage():
    global stats
    """Return the CPU usage percentage of the current process."""
    #process = psutil.Process(os.getpid())
    stats['cpu_one_core'] = stats['process_pointer'].cpu_percent(interval=stats['refresh_interval'])     # cpu usage averaged over 10 seconds
    return round(stats['cpu_one_core'] / stats['nr_cpu_cores'], 1)

#stats thread
def start_stats():
    global stats,buffered_feedback, signal

    stats['process_pointer'] = psutil.Process(os.getpid())

    while False:

        stats['cpu'] = get_process_cpu_usage()  # cpu usage for the complete processor # ({stats['cpu_one_core']}/{stats['nr_cpu_cores']})
        if buffered_feedback['acc']:
        # if False:
            acc = buffered_feedback['acc'][-1]
            x = acc['x']
            y = acc['y']
            z = acc['z']
            acc = f" | {x:<18.16f} {y:<18.16f} {z:<18.16f}"
        else:
            acc = ""


        if True:
            cpu = f" | cpu: {stats['cpu']:>4.1f}%"

        if True:
            si = f" | signal: {signal['is_good']}"

        if True:
            if buffered_data['eeg']:
                rec = "rec "
            else:
                rec = "wait"
            
        if True:
            m = round(stats['process_pointer'].memory_percent(),1)
            mem = f" | mem: {m}%"

        # cpu usage, received osc streams, good fit
        sys.stdout.write(f"\r{stats['counter']} {rec}{cpu}{mem}{acc}{si} ")
        sys.stdout.flush()


        if stats['counter'] == '-':
            stats['counter'] = '+'
        else:
            stats['counter'] = '-'


        # waits automatically because of get_process_cpu_usage()
        #time.sleep(stats['refresh_interval'])





def parse_arguments():
    parser = argparse.ArgumentParser(description='Configure EEG recording parameters.')

    # Define command-line arguments for each configuration parameter
    # parser.add_argument('--only_record_if_signal_is_good', action='store_false',
    # parser.add_argument('--only_record_if_signal_is_good', type=bool, default=True,
    parser.add_argument('--only_record_if_signal_is_good', type=bool, default=False, choices=[0, 1],
                        help='Default 0. Record osc only if all sensors have good signal quality.')
    parser.add_argument('--if_signal_is_not_good_set_signal_to', type=str, default='record_received_signal',
                        choices=['NaN', '0.0', 'record_received_signal'],
                        help='Default "record_received_signal". The Muse device has a Signal Quality marker, that will be 0 if the Signal is bad/not received correctly. set to "record_received_signal" to handle afterwards (most flexible). Substitue with this value (NaN = no data received marker, 0.0 = blank value), but you might lose contextual information. "record_received_signal" will save the received value, even though it is most likely an artifact, needs more processing after recording.')
    parser.add_argument('--add_heart_rate_file', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add separate file for heart rate.')
    parser.add_argument('--add_acc_file', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add separete file for accelaration (gryoscope) value.')
    parser.add_argument('--add_signal_quality_file', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add signal quality file. each row corresponds to the same row in the eeg file. they are separate to keep the fileformat compatable with eeglab.')
    parser.add_argument('--add_signal_quality_for_each_electrode', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add signal quality column for each electrode.')
    parser.add_argument('--add_aux_columns', type=bool, default=False, choices=[0, 1],
                        help='Default 0. Add auxiliary columns (aux0 and aux1).')
    parser.add_argument('--add_time_column', type=bool, default=False, choices=[0, 1],
                        help='Default 1. Add a time column, but some programms like EegLab do not use a tome column.')
    parser.add_argument('--use_tabseparator_for_csv', type=bool, default=False, choices=[0, 1],
                        help='Default 0. Use tab as separator in CSV. Set to 0 for comma separator (default).')
    parser.add_argument('--add_header_row', type=bool, default=False, choices=[0, 1],
                        help='Default 1. Add header row, but EegLab doesnt accept a header row.')
    parser.add_argument('--port', type=int, default=5000,
                        help='Default 5000. Port number for the server.')
    parser.add_argument('--ip', type=str, default='0.0.0.0',
                        help='Default "0.0.0.0". IP address for the server to listen to. "0.0.0.0" listens to all ip addresses.')
    parser.add_argument('--file_name_prefix', type=str, default='eeg_',
                        help='Default "eeg_". File name prefix for output files.')
    parser.add_argument('--feedback_acc', type=bool, default=True,
                        help='Default 0. Use the Accelerometer data to find sleepiness.')

    return parser.parse_args()


def init_conf():
    global conf, columns, sig
    # Parse command-line arguments

    args = parse_arguments()

    # Create a configuration dictionary with the parsed arguments
    conf = {
        'only_record_if_signal_is_good': args.only_record_if_signal_is_good,
        'if_signal_is_not_good_set_signal_to': args.if_signal_is_not_good_set_signal_to,
        'add_heart_rate_file': args.add_heart_rate_file,
        'add_acc_file': args.add_acc_file,
        'add_signal_quality_file': args.add_signal_quality_file,
        'add_signal_quality_for_each_electrode': args.add_signal_quality_for_each_electrode,
        'add_aux_columns': args.add_aux_columns,
        'use_tabseparator_for_csv': args.use_tabseparator_for_csv,
        'add_time_column': args.add_time_column,
        'add_header_row': args.add_header_row,
        'port': args.port,
        'ip': args.ip,
        'file_name_prefix': args.file_name_prefix,
        'feedback_acc': args.feedback_acc,
    }

    if conf['add_time_column']:
        columns['eeg'].append('timestamp')
        columns['heart_rate'].append('timestamp')
        columns['acc'].append('timestamp')
        columns['signal_quality'].append('timestamp')


    # Define the CSV column names based on OSC addresses
    columns['eeg'].extend(["tp9", "af7", "af8", "tp10"])
    #columns['heart_rate'].extend(["heart_rate_0", "heart_rate_1", "heart_rate_2"])
    columns['heart_rate'].extend(["heart_rate_1"]) # muse only uses heart rate sensor 1, sensor 0 & 2 (infrared and green) are not used, mind monitor does not send the heartrate at all
    columns['acc'].extend(["x", "y", "z"])
    columns['signal_quality'].extend(["all_signals_are_good"])

    if conf['add_aux_columns']:
        columns['eeg'].extend(['aux0', 'aux1'])

    if conf['add_signal_quality_for_each_electrode']:
        columns['signal_quality'].extend(['signal_quality_TP9', 'signal_quality_AF7', 'signal_quality_AF8', 'signal_quality_TP10'])

    stats['nr_cpu_cores'] = psutil.cpu_count(logical=True)

    conf['exiting'] = False # marker for threads that the programm is exiting



class MovingGraph:
    def __init__(self, window_size=20, update_interval=500, ylim=(-1, 1)):
        """
        Initialize the MovingGraph object.

        :param window_size: Size of the time window in seconds for which data is displayed.
        :param update_interval: Update interval in milliseconds.
        :param ylim: Tuple for y-axis limits.
        """
        self.window_size = window_size
        self.update_interval = update_interval
        self.ylim = ylim

        # Number of data points based on update interval
        self.num_points = int(window_size * 1000 / update_interval)

        # Initialize data buffer
        self.data_buffer = np.zeros((self.num_points, 3))

        # Setup the plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, self.window_size)
        self.ax.set_ylim(self.ylim)

        # Initialize lines
        self.line_x, = self.ax.plot([], [], label='X axis')
        self.line_y, = self.ax.plot([], [], label='Y axis')
        self.line_z, = self.ax.plot([], [], label='Z axis')
        self.ax.legend()

        # Animation setup
        self.ani = FuncAnimation(self.fig, self._update, init_func=self._init, blit=True, interval=self.update_interval)

        plt.show(block=False)  # Non-blocking show

    def _init(self):
        """Initialization function for animation."""
        self.line_x.set_data([], [])
        self.line_y.set_data([], [])
        self.line_z.set_data([], [])
        return self.line_x, self.line_y, self.line_z,

    def _update(self, frame):
        """Update function for animation."""
        time = np.linspace(0, self.window_size, len(self.data_buffer))
        self.line_x.set_data(time, self.data_buffer[:, 0])
        self.line_y.set_data(time, self.data_buffer[:, 1])
        self.line_z.set_data(time, self.data_buffer[:, 2])
        return self.line_x, self.line_y, self.line_z,

    def update(self, x, y, z):
        """
        Update the graph with new x, y, z values.

        :param x: New x-axis value
        :param y: New y-axis value
        :param z: New z-axis value
        """
        # Roll the buffer to make room for new data and add new data
        self.data_buffer = np.roll(self.data_buffer, -1, axis=0)
        self.data_buffer[-1] = [x, y, z]


# Your feedback_acc function remains mostly the same, but ensure it's using this updated calculate_movement

# biofeedback thread
def feedback_acc():
    global buffered_feedback, signal
    # time.sleep(2)

    graph = MovingGraph(ylim=(-0.05, 0.05))

    while True:

        if buffered_feedback['acc']:
            # Initialize previous values with None or some initial values
            prev_x, prev_y, prev_z = None, None, None

            # List to store relative movements
            relative_movements = []


            for acc in buffered_feedback['acc']:
                # Extract x, y, z from the dictionary
                x, y, z = acc['x'], acc['y'], acc['z']

                # Calculate relative movement
                if prev_x is not None:
                    # Calculate the difference from the previous reading
                    dx = x - prev_x
                    dy = y - prev_y
                    dz = z - prev_z

                    # Store the relative movement
                    relative_movements.append({'dx': dx, 'dy': dy, 'dz': dz})
                else:
                    # For the first iteration, we can't calculate a difference, so we might
                    # choose to either skip this, set to zero, or use the current values directly
                    # Here, setting to zero for consistency with no movement concept:
                    relative_movements.append({'dx': 0, 'dy': 0, 'dz': 0})

                # Update previous values for next iteration
                prev_x, prev_y, prev_z = x, y, z

            # Summing up all relative movements
            sum_dx = sum(abs(item['dx']) for item in relative_movements)
            sum_dy = sum(abs(item['dy']) for item in relative_movements)
            sum_dz = sum(abs(item['dz']) for item in relative_movements)

            # Calculating the average
            # First, check if relative_movements is not empty to avoid division by zero
            if relative_movements:
                count = len(relative_movements)
                avg_dx = sum_dx / count
                avg_dy = sum_dy / count
                avg_dz = sum_dz / count
            else:
                avg_dx, avg_dy, avg_dz = 0, 0, 0

                # After processing all data, get the total movement

            #if signal['is_good']:

            # sys.stdout.write(f"\r{avg_dx:18.16f}   {avg_dy:18.16f}    {avg_dz:18.16f}            \n")
            # sys.stdout.flush()

            graph.update(avg_dx, avg_dy, avg_dz)
            plt.pause(0.001)  # Allow plot to update


            buffered_feedback['acc'].clear()
        time.sleep(.5)

def open_file(name, csv_delimiter=','):
    global file, folder, conf

    file['open'][name] = open(f"{folder['out']}/{folder['tmp']}/{file['name'][name]}", "w", newline="")
    file['csv_writer'][name] = csv.DictWriter(file['open'][name], fieldnames=columns[name], delimiter=csv_delimiter)
    if conf['add_header_row']:
        file['csv_writer'][name].writeheader()


def write_to_file(name):
    global buffered_data, last_timestamp, file, conf

    current_timestamp = 0

    try:
        if name == 'signal_quality':
            sr = sampling_rate['eeg']
        else:
            sr = sampling_rate[name]

        for i, b in enumerate(buffered_data[name]):
            if conf['add_time_column']:
                current_timestamp = last_timestamp[name] + i / sr * 1000
                b['timestamp'] = round(current_timestamp, 4)
            file['csv_writer'][name].writerow(b)
            file['open'][name].flush()

        if conf['add_time_column']:
            last_timestamp[name] = current_timestamp + (1 / sr * 1000)

        buffered_data[name].clear()
    except Exception as e:
        if conf['exiting'] != True:
            print(f'    !! 10s of *{name}* data lost !!  ')

def create_folder(f):
    try:
        # Check if the directory exists, if not, create it
        if not os.path.exists(f):
            os.makedirs(f)
        return True
    except OSError as error:
        print(f"Error: Creating directory {f}. {error}")
        return False



# Function to write buffered data to a file every 10 seconds
def process_buffers():
    global buffered_data, columns, start_time, sampling_rate, conf, file, folder, last_timestamp

    time.sleep(1)

    last_received_time = None


    if conf['use_tabseparator_for_csv']:
        csv_delimiter = '\t'
    else:
        csv_delimiter = ','

    while True:
        # print(heart_rate)

        now = time.time()
        # print(status_isGood)
        # print(status_electrodeFit)

        if buffered_data['eeg']:

            if last_received_time is None:
                current_timestamp_str = time.strftime("%Y.%m.%d_%H.%M")
                folder['tmp'] = f"{conf['file_name_prefix']}{current_timestamp_str}"
                file['name']['eeg'] = f"{conf['file_name_prefix']}{current_timestamp_str}_eeg.csv"
                file['name']['heart_rate'] = f"{conf['file_name_prefix']}{current_timestamp_str}_heart_rate.csv"
                file['name']['acc'] = f"{conf['file_name_prefix']}{current_timestamp_str}_accelerator.csv"
                file['name']['signal_quality'] = f"{conf['file_name_prefix']}{current_timestamp_str}_signal_quality.csv"
                create_folder(folder['out'])
                create_folder(f"{folder['out']}/{folder['tmp']}")

                open_file('eeg', csv_delimiter=csv_delimiter)

                if conf['add_heart_rate_file']:
                    open_file('heart_rate', csv_delimiter=csv_delimiter)

                if conf['add_acc_file']:
                    open_file('acc', csv_delimiter=csv_delimiter)

                if conf['add_signal_quality_file']:
                    open_file('signal_quality', csv_delimiter=csv_delimiter)

                # print('new file created:')
                # print(f" {folder['tmp']} created")
                sys.stdout.write(f"\r {folder['tmp']} created.                     \n")
                sys.stdout.flush()

            write_to_file('eeg')


            if conf['add_heart_rate_file']:
                write_to_file('heart_rate')

            if conf['add_acc_file']:
                write_to_file('acc')

            if conf['add_signal_quality_file']:
                write_to_file('signal_quality')

            last_received_time = time.time()

        # zip file after 10min inactivity and remove plain csv
        else:
            if last_received_time is not None and last_received_time + 5 * 60 < now:
                try:


                    start_time = None
                    last_timestamp['eeg'] = 0
                    last_timestamp['heart_rate'] = 0
                    last_timestamp['acc'] = 0
                    last_timestamp['signal_quality'] = 0

                    last_received_time = None

                    close_and_zip_files()



                except Exception as e:
                    print(' Warning: recoded file not found.. ')



        #print_stats()
        time.sleep(10)


def close_and_zip_files():
    global file, folder, buffered_data, buffered_feedback

    try:
        for f in file['open']:
            file['open'][f].close()

        sys.stdout.write(f"\r  files are beeing compressed. please wait a short while..                   ")
        sys.stdout.flush()

        # Create a ZIP file with normal compression
        zip_file_name = f"{folder['tmp']}.zip"
        ff = []
        with zipfile.ZipFile(f"{folder['out']}/{zip_file_name}", 'w', zipfile.ZIP_DEFLATED) as zipf:
            # pack all created files that are > 0 Bytes
            for f in file['name']:
                ff.append(f"{folder['out']}/{folder['tmp']}/{file['name'][f]}")
                #print(ff[-1])
                if os.path.getsize(ff[-1]) > 0:
                    zipf.write(ff[-1], arcname=os.path.basename(ff[-1]))

        # Delete the original files
        for f in ff:
            os.remove(f)
        # remove tmp folder
        os.rmdir(f"{folder['out']}/{folder['tmp']}")

        # clear file list and tmp folder name
        for f in file['name']:
            file['name'][f] = ''
        folder['tmp'] = ''

        # clear buffers (in case they where not used completly)
        for b in buffered_data:
            buffered_data[b].clear()
        for b in buffered_feedback:
            buffered_feedback[b].clear()

        sys.stdout.write(f"\r+{zip_file_name} saved.                     \n")
        sys.stdout.flush()
        # print(f'\n  {zip_file_name} saved.')

    except Exception as e:
        print(' Warning: recoded file not found.. \n', e)
def gracefully_end():
    global conf

    conf['exiting'] = True

    if folder['tmp'] != '':
        close_and_zip_files()

    print('\nend programm. all good.')




def main():



    #keyboard.on_press(on_press)    #needs root on android

    # Collect events until released
    def start_input():
        #time.sleep(2)
        while True:
            user_input = input("  --> Exit: x (+Enter) | note: n | s = stats       \n")
            sys.stdout.flush()
       
            if user_input == 'x':
                gracefully_end()
                os._exit(0)

            sys.stdout.write(f"\rYou typed: {user_input}                      \n")
            sys.stdout.flush()

    stats_thread = threading.Thread(target=start_stats)
    stats_thread.start()

    # pycharm has problems with the input.. works great in termux
    if not is_run_in_pycharm():
        input_thread = threading.Thread(target=start_input)
        input_thread.start()

    # Starting the separate thread  for writing to file
    write_thread = threading.Thread(target=process_buffers, daemon=True)
    write_thread.start()

     # Starting the separate thread  for writing to file
    osc_thread = threading.Thread(target=osc_start, daemon=True)
    osc_thread.start()

    # if conf['feedback_acc']:
    #      # Starting the separate thread  for writing to file
    #     feedback_thread = threading.Thread(target=feedback_acc, daemon=True)
    #     feedback_thread.start()

    while True:
        feedback_acc()
        time.sleep(1)



if __name__ == '__main__':
    init_conf()
    main()
