import os
import sys

import psutil





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


def get_process_cpu_usage(data):

    """Return the CPU usage percentage of the current process."""
    # process = psutil.Process(os.getpid())
    data['stats']['cpu_one_core'] = data['stats']['process_pointer'].cpu_percent(
        interval=data['stats']['refresh_interval'])  # cpu usage averaged over 10 seconds
    return round(data['stats']['cpu_one_core'] / data['stats']['nr_cpu_cores'], 1)


# stats thread
def start_stats(data):


    data['stats']['nr_cpu_cores'] = psutil.cpu_count(logical=True)
    data['stats']['process_pointer'] = psutil.Process(os.getpid())

    while True:

        # cpu usage for the complete processor # ({data['stats']['cpu_one_core']}/{data['stats']['nr_cpu_cores']})
        data['stats']['cpu'] = get_process_cpu_usage(data)

        si = rec = acc = cpu = nod = mem = ''
        if False:
            if data['feedback']['acc']:
                # if False:
                a = data['feedback']['acc'][-1]
                x = a['x']
                y = a['y']
                z = a['z']
                acc = f" | {x:<18.16f} {y:<18.16f} {z:<18.16f}"


        if True:
            #cpu = f" | 1cpu: {data['stats']['cpu_one_core']:>4.1f}%"
            cpu = f" | ∑cpu: {data['stats']['cpu']:>4.1f}%"

        if False:
            si = f" | signal: {data['signal']['is_good']}"

        if True:
            if not data['buffer']['eeg'].empty():
                rec = "rec "
            else:
                rec = "wait"

        if True:
            #m = round(data['stats']['process_pointer'].memory_percent(), 1)
            mem_info = data['stats']['process_pointer'].memory_info()
            # Convert bytes to megabytes
            m = round(mem_info.rss / (1024 ** 2),0)
            mem = f" | mem: {m:3.0f}MB"

        if data['conf']['feedback_acc']:
            try:
                #nod = f" | nod: {data['stats']['nod']:<18.16f}"
                nod = f" | nod: {data['stats']['moved_sum']}"

            except Exception as e:
                pass



        # cpu usage, received osc streams, good fit
        sys.stdout.write(f"\r{data['stats']['counter']} {rec}{cpu}{mem}{acc}{si}{nod} ")
        sys.stdout.flush()

        if data['stats']['counter'] == '-':
            data['stats']['counter'] = '+'
        else:
            data['stats']['counter'] = '-'

        # waits automatically because of get_process_cpu_usage()
        # time.sleep(data['stats']['refresh_interval'])

