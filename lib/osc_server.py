import os
from functools import partial

from pythonosc import dispatcher
from pythonosc import osc_server

import math




# Define the function to handle incoming OSC messages
def handle_eeg_message( buffer_eeg, signal, conf, address, *args):

    eeg_data = {}

    args = list(args)  # convert tuple to list
    if conf['if_signal_is_not_good_set_signal_to'] != 'record_received_signal':
        for i, arg in enumerate(args):
            if (math.isnan(args[i])):
                args[i] = conf['if_signal_is_not_good_set_signal_to']
            else:
                args[i] = arg



    eeg_data["tp9"] = args[0]
    eeg_data["af7"] = args[1]
    eeg_data["af8"] = args[2]
    eeg_data["tp10"] = args[3]

    # only add the first 4 sensors if aux0/1 is not wanted
    if conf['add_aux_columns'] == True:
        eeg_data["aux0"] = args[4]
        eeg_data["aux1"] = args[5]



    if conf['only_record_if_signal_is_good'] == True:
        sEl = 0
        for el in signal['electrode']:
            sEl += el
        # the signal is only good if all 4 electrodes have good fit (each is 1) and ica is 1
        if signal['ica_good'] != 1 and sEl != 4:
            return

    buffer_eeg.put(eeg_data)


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


def handle_ica_message( buffer_ica, signal, address, *args):
    # thread save variable assignment (locked)
    signal['ica_good'] = args[0]
    buffer_ica.put({'ica':args[0]})


def handle_electrodeFit_message(buffer_signal_quality, signal, address, *args):

    el = []
    co = ['tp9', 'af7', 'af8', 'tp10']
    sq = {}
    for i, arg in enumerate(args):
        el.append(int(arg))
        sq[co[i]] = int(arg)

    # thread save variable assignment (locked)
    signal['electrode'] = el

    buffer_signal_quality.put(sq)

def handle_drlref_message(buffer_drlref, address, *args):

    el = []
    co = ['drl', 'ref']
    re = {}
    for i, arg in enumerate(args):
        el.append(arg)
        re[co[i]] = arg
    # thread save variable assignment (locked)
    buffer_drlref.put(re)


# this is not completely correct, since it will put the ica value whenever blink is streamed
# (so theoretically jaw and forehead could always be sent on the next put, depending on which signal is received first..)
# but i think its negletable, to really solve it is a bit more complicated i think..
def handle_icaMM_message( buffer_ica, signal, type, address, *args):

    opt = ['blink', 'jaw_clench', 'touching_forehead' ]

    signal[type] = (int(args[0]))

    sum = 0
    for o in opt:
        sum += signal[o]

    if sum == 0:
        signal['ica_good'] = 1
    else:
        signal['ica_good'] = 0

    if type == opt[0]:
        buffer_ica.put(signal['ica_good'])



def osc_start(data):
    global dispatcher

    dispatcher = dispatcher.Dispatcher()
    # muse app osc streams
    dispatcher.map("/eeg", partial(handle_eeg_message,  data['buffer']['eeg'], data['signal'], data['conf']))  # muse app osc      buffer_eeg, buffer_signal_quality, data_signal, conf
    if data['conf']['add_heart_rate_file']:
        dispatcher.map("/ppg", partial(handle_ppg_message, data['buffer']['heart_rate'], data['conf']))  # muse app osc
    if data['conf']['add_acc_file']:
        dispatcher.map("/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf']))  # muse app osc               buffer_acc, feedback_acc, conf):

    if data['conf']['add_ica_file']:
        dispatcher.map("/is_good", partial(handle_ica_message, data['buffer']['ica'], data['signal'], ))  # muse app
    if data['conf']['add_signal_quality_file']:
        dispatcher.map("/hsi", partial(handle_electrodeFit_message, data['buffer']['signal_quality'], data['signal'], ))  # muse app
    if data['conf']['add_drlref_file']:
        dispatcher.map("/drlref", partial(handle_drlref_message, data['buffer']['drlref'], ))  # muse app


    # mind monitor osc streams
    dispatcher.map("/muse/eeg", partial(handle_eeg_message, data['buffer']['eeg'], data['buffer']['signal_quality'], data['signal'], data['conf']))  # mind monitor osc
    if data['conf']['add_acc_file']:
        dispatcher.map("/muse/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf']))  # muse app osc
    if data['conf']['add_signal_quality_file']:
        dispatcher.map("/muse/elements/horseshoe", partial(handle_electrodeFit_message, data['signal'], ))  # mind monitor osc
    # a bit tricky, because mindmonitor splits the ica into 3 parts..
    # if data['conf']['add_ica_file']:
        dispatcher.map("/muse/elements/blink", partial(handle_icaMM_message, 'blink', data['signal'], ))  # mind monitor osc
        dispatcher.map("/muse/elements/jaw_clench", partial(handle_icaMM_message, 'jaw_clench', data['signal'], ))  # mind monitor osc
        dispatcher.map("/muse/elements/touching_forehead", partial(handle_icaMM_message, 'touching_forehead', data['signal'], ))  # mind monitor osc
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

