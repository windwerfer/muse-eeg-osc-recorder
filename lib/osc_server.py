import os

from pythonosc import dispatcher
from pythonosc import osc_server

import math



# Define the function to handle incoming OSC messages
def handle_eeg_message(address, *args, timestamp_true=False, timestamp_constant=True):
    global columns, start_time, conf, signal, electrodes, debug_print

    eeg_data = {}
    sig_data = {}

    # if conf['add_time_column']:
    #     eeg_data["timestamp"] = None  # placeholder, will be set before writing to file

    args = list(args)  # convert tuple to list
    if conf['if_signal_is_not_good_set_signal_to'] != 'record_received_signal':
        for i, arg in enumerate(args):
            if (math.isnan(args[i])):
                args[i] = conf['if_signal_is_not_good_set_signal_to']
            else:
                args[i] = arg

            # handle case: signal is not good. no_change -> write the wrong value, 0.0 -> write 0.0 as value (should no mess up the calculations)
            if signal['is_good'] != 1:
                args[i] = conf['if_signal_is_not_good_set_signal_to']

    eeg_data["tp9"] = args[0]
    eeg_data["af7"] = args[1]
    eeg_data["af8"] = args[2]
    eeg_data["tp10"] = args[3]

    # only add the first 4 sensors if aux0/1 is not wanted
    if conf['add_aux_columns'] == True:
        eeg_data["aux0"] = args[4]
        eeg_data["aux1"] = args[5]

    if conf['add_signal_quality_file']:
        sig_data['all_signals_are_good'] = signal['is_good']

        if conf['add_signal_quality_for_each_electrode']:
            sig_data['signal_quality_TP9'] = signal['electrode'][0]
            sig_data['signal_quality_AF7'] = signal['electrode'][1]
            sig_data['signal_quality_AF8'] = signal['electrode'][2]
            sig_data['signal_quality_TP10'] = signal['electrode'][3]

    if conf['only_record_if_signal_is_good'] == True:
        if signal['is_good'] != 1:
            return

    buffered_data['eeg'].append(eeg_data)
    if conf['add_signal_quality_file']:
        buffered_data['signal_quality'].append(sig_data)

    if (debug_print):
        print(f"Received EEG OSC message - Address: {address}, Args: {args}")


def handle_ppg_message(address, *args):
    global buffered_data

    ppg_data = {}

    args = list(args)  # convert tuple to list
    if conf['if_signal_is_not_good_set_signal_to'] != 'record_received_signal':
        for i, arg in enumerate(args):
            if (math.isnan(args[i])):
                args[i] = conf['if_signal_is_not_good_set_signal_to']
            else:
                args[i] = arg

    # muse app only uses heart rate sensor 1, sensor 0 & 2 (infrared and green) are not used, mind monitor does not send the heartrate at all
    #ppg_data['heart_rate_0'] = args[0]     # ignored, because its constantly nan
    ppg_data['heart_rate_1'] = args[1]
    #ppg_data['heart_rate_2'] = args[2]

    buffered_data['heart_rate'].append(ppg_data)


def handle_acc_message(address, *args):
    global buffered_data, buffered_feedback

    acc_data = {}

    # if conf['add_time_column']:
    #     acc_data["timestamp"] = None  # placeholder, will be set before writing to file
    acc_data['x'] = args[0]
    acc_data['y'] = args[1]
    acc_data['z'] = args[2]

    buffered_data['acc'].append(acc_data)
    if conf['feedback_acc']:
        buffered_feedback['acc'].append(acc_data)


def handle_isGood_message(address, *args):
    global signal

    signal['is_good'] = args[0]


def handle_electrodeFit_message(address, *args):
    global signal

    for i, arg in enumerate(args):
        signal['electrode'][i] = arg


def handle_isGoodMM_message(address, *args):
    global signal

    for i, arg in enumerate(args):
        signal['electrode'][i] = arg

    sum = 0
    for a in signal['electrode']:
        sum += a
    if sum == 4:
        signal['is_good'] = 1
    else:
        signal['is_good'] = 0


def osc_start():
    global dispatcher

    dispatcher = dispatcher.Dispatcher()
    # muse app osc streams
    dispatcher.map("/eeg", handle_eeg_message)  # muse app osc
    if conf['add_heart_rate_file']:
        dispatcher.map("/ppg", handle_ppg_message)  # muse app osc
    if conf['add_acc_file']:
        dispatcher.map("/acc", handle_acc_message)  # muse app osc

    if conf['add_signal_quality_file']:
        dispatcher.map("/is_good", handle_isGood_message)  # muse app osc
        if conf['add_signal_quality_for_each_electrode']:
            dispatcher.map("/hsi", handle_electrodeFit_message)  # muse app osc


    # mind monitor osc streams
    dispatcher.map("/muse/eeg", handle_eeg_message)  # mind monitor osc
    if conf['add_acc_file']:
        dispatcher.map("/muse/acc", handle_acc_message)  # muse app osc
    if conf['add_signal_quality_file']:
        dispatcher.map("/muse/elements/horseshoe", handle_isGoodMM_message)  # mind monitor osc

    server = osc_server.ThreadingOSCUDPServer((conf['ip'], conf['port']), dispatcher)

    print(f"Listening on port {conf['port']} for OSC messages... ")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        gracefully_end()
        os._exit(0)
    finally:
        #keyboard.unhook_all()
        pass

