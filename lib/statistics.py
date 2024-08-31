import os
import sys

import psutil


stats = {'refresh_interval': 0.5, 'cpu': 0, 'cpu_one_core': 0.0, 'nr_cpu_cores': 1, 'battery': None, 'recording': 0,
         'counter': '-'}
stats['nr_cpu_cores'] = psutil.cpu_count(logical=True)

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
    # process = psutil.Process(os.getpid())
    stats['cpu_one_core'] = stats['process_pointer'].cpu_percent(
        interval=stats['refresh_interval'])  # cpu usage averaged over 10 seconds
    return round(stats['cpu_one_core'] / stats['nr_cpu_cores'], 1)


# stats thread
def start_stats():
    global stats, buffered_feedback, signal

    stats['process_pointer'] = psutil.Process(os.getpid())

    while False:

        stats[
            'cpu'] = get_process_cpu_usage()  # cpu usage for the complete processor # ({stats['cpu_one_core']}/{stats['nr_cpu_cores']})
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
            m = round(stats['process_pointer'].memory_percent(), 1)
            mem = f" | mem: {m}%"

        # cpu usage, received osc streams, good fit
        sys.stdout.write(f"\r{stats['counter']} {rec}{cpu}{mem}{acc}{si} ")
        sys.stdout.flush()

        if stats['counter'] == '-':
            stats['counter'] = '+'
        else:
            stats['counter'] = '-'

        # waits automatically because of get_process_cpu_usage()
        # time.sleep(stats['refresh_interval'])

