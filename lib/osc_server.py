import os
from functools import partial

from pythonosc import dispatcher
from pythonosc import osc_server

import math




# Define the function to handle incoming OSC messages
def handle_eeg_message( buffer_eeg, buffer_signal_quality, signal, conf, address, *args):

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
        sig_data['signal_quality_is_good'] = signal['is_good']

        if conf['add_signal_quality_for_each_electrode']:
            sig_data['signal_quality_tp9'] = signal['electrode'][0]
            sig_data['signal_quality_af7'] = signal['electrode'][1]
            sig_data['signal_quality_af8'] = signal['electrode'][2]
            sig_data['signal_quality_tp10'] = signal['electrode'][3]

    if conf['only_record_if_signal_is_good'] == True:
        if signal['is_good'] != 1:
            return

    buffer_eeg.put(eeg_data)
    if conf['add_signal_quality_file']:
        buffer_signal_quality.put(sig_data)

    if False:
        print(f"Received EEG OSC message - Address: {address}, Args: {args}")


def handle_ppg_message( buffer_ppg, conf, address, *args):

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

    buffer_ppg.put(ppg_data)


def handle_acc_message( buffer_acc, feedback_acc, conf, address, *args):

    acc_data = {}

    # if conf['add_time_column']:
    #     acc_data["timestamp"] = None  # placeholder, will be set before writing to file
    acc_data['x'] = args[0]
    acc_data['y'] = args[1]
    acc_data['z'] = args[2]

    buffer_acc.put(acc_data)
    if conf['feedback_acc']:
        feedback_acc.put(acc_data)


def handle_isGood_message( signal, address, *args):
    # thread save variable assignment (locked)
    signal['is_good'] = args[0]


def handle_electrodeFit_message(signal, address, *args):

    el = []
    for i, arg in enumerate(args):
        el.append(int(arg))
    # thread save variable assignment (locked)
    signal['electrode'] = el


def handle_isGoodMM_message( signal, address, *args):

    el = []
    for i, arg in enumerate(args):
        el.append(int(arg))
    # thread save variable assignment (locked)
    signal['electrode'] = el

    sum = 0
    for a in el:
        sum += a
    if sum == 4:
        # thread save variable assignment (locked)
        signal['is_good'] = 1
    else:
        # thread save variable assignment (locked)
        signal['is_good'] = 0


def osc_start(data):
    global dispatcher

    dispatcher = dispatcher.Dispatcher()
    # muse app osc streams
    dispatcher.map("/eeg", partial(handle_eeg_message,  data['buffer']['eeg'], data['buffer']['signal_quality'], data['signal'], data['conf']))  # muse app osc      buffer_eeg, buffer_signal_quality, data_signal, conf
    if data['conf']['add_heart_rate_file']:
        dispatcher.map("/ppg", partial(handle_ppg_message, data['buffer']['heart_rate'], data['conf']))  # muse app osc
    if data['conf']['add_acc_file']:
        dispatcher.map("/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf']))  # muse app osc               buffer_acc, feedback_acc, conf):

    if data['conf']['add_signal_quality_file']:
        dispatcher.map("/is_good", partial(handle_isGood_message, data['signal'], ))  # muse app osc
        if data['conf']['add_signal_quality_for_each_electrode']:
            dispatcher.map("/hsi", partial(handle_electrodeFit_message, data['signal'], ))  # muse app osc


    # mind monitor osc streams
    dispatcher.map("/muse/eeg", partial(handle_eeg_message, data['buffer']['eeg'], data['buffer']['signal_quality'], data['signal'], data['conf']))  # mind monitor osc
    if data['conf']['add_acc_file']:
        dispatcher.map("/muse/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf']))  # muse app osc
    if data['conf']['add_signal_quality_file']:
        dispatcher.map("/muse/elements/horseshoe", partial(handle_isGoodMM_message, data['signal'], ))  # mind monitor osc

    server = osc_server.BlockingOSCUDPServer((data['conf']['ip'], data['conf']['port']), dispatcher)

    print(f"Listening on port {data['conf']['port']} for OSC messages... ")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        #gracefully_end()
        #os._exit(0)
        pass
    finally:
        #keyboard.unhook_all()
        pass

