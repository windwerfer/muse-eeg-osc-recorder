import os
import time
from functools import partial

from pythonosc import dispatcher
from pythonosc import osc_server

import math




# Define the function to handle incoming OSC messages
def handle_eeg_message( buffer_eeg, buffer_signal, buffer_ica, buffer_drlref, signal, conf, stream, address, *args):

    # define if received from muse_app or mindmonitor_app
    if address == '/eeg' :
        stream['from_muse_app'] = 1
        stream['from_mindmonitor_app'] = 0
        # if conf['no_auto_split_if_muse_app'] == 1, contiuous recording enabled

    else:
        stream['from_muse_app'] = 0
        stream['from_mindmonitor_app'] = 1


    if stream['from_muse_app'] == 1:
        # only record if feedback is going on
        if stream['rec'] == 0 and stream['calibrate'] == 0:
            return
        # check if muse_app is still sending feedback, or if it stopped
        if stream['last_data_received'] + 1 < time.time():
            stream['rec'] = 0
            stream['calibrate'] = 0
            return



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
        if signal['ica_good'] != 1 or sEl != 4:
            return

    buffer_eeg.put(eeg_data)

    # add signal_quality data:
    # it is processed here to keep it in sync with the eeg data,
    # the signal quality data does not update with the same frequency as eeg data
    # this will maybe double the filesize of the signal data, but i find it better to have the signal quality
    # exactly match the eeg data
    if not conf['no_signal_quality_file']:
        sig = {
                'tp9':signal['electrode'][0],
                'af7':signal['electrode'][1],
                'af8':signal['electrode'][2],
                'tp10':signal['electrode'][3]
                }
        buffer_signal.put(sig)

    # add ica file (same as signal quality)
    if not conf['no_ica_file']:
        buffer_ica.put({'ica':signal['ica_good']})

    # add drlref file (same as signal quality)
    if not conf['no_drlref_file']:
        drlref = {
                'drl':signal['drlref'][0],
                'ref':signal['drlref'][1]
                }
        buffer_drlref.put(drlref)

    if False:
        print(f"Received EEG OSC message - Address: {address}, Args: {args}")


def handle_ppg_message( buffer_ppg, conf, stream, address, *args):

    if stream['from_muse_app'] == 1:
        # only record if feedback is going on
        if stream['rec'] == 0 and stream['calibrate'] == 0:
            return

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


def handle_acc_message( buffer_acc, feedback_acc, conf, stream, address, *args):

    if stream['from_muse_app'] == 1:
        # only record if feedback is going on
        if stream['rec'] == 0 and stream['calibrate'] == 0:
            return

    acc_data = {}

    # if conf['add_time_column']:
    #     acc_data["timestamp"] = None  # placeholder, will be set before writing to file
    acc_data['x'] = args[0]
    acc_data['y'] = args[1]
    acc_data['z'] = args[2]

    buffer_acc.put(acc_data)
    if conf['feedback_acc']:
        feedback_acc.put(acc_data)


def handle_ica_message( buffer_ica, signal, stream, address, *args):

    # if stream['from_muse_app'] == 1:
    #     # only record if feedback is going on
    #     if stream['rec'] == 0 and stream['calibrate'] == 0:
    #         return

    # thread save variable assignment (locked)
    signal['ica_good'] = args[0]
    # buffer_ica.put({'ica':args[0]})


def handle_electrodeFit_message(buffer_signal_quality, signal, stream, address, *args):

    # if stream['from_muse_app'] == 1:
    #     # only record if feedback is going on
    #     if stream['rec'] == 0 and stream['calibrate'] == 0:
    #         return


    el = []
    # co = ['tp9', 'af7', 'af8', 'tp10']
    # sq = {}
    for i, arg in enumerate(args):
        el.append(int(arg))
        # sq[co[i]] = int(arg)

    # thread save variable assignment (locked)
    signal['electrode'] = el

    # buffer_signal_quality.put(sq)

def handle_drlref_message(buffer_drlref, signal, stream, address, *args):

    # if stream['from_muse_app'] == 1:
    #     # only record if feedback is going on
    #     if stream['rec'] == 0 and stream['calibrate'] == 0:
    #         return

    el = []
    # co = ['drl', 'ref']
    # re = {}
    for i, arg in enumerate(args):
        el.append(arg)
        # re[co[i]] = arg

    signal['drlref'] = el

    # buffer_drlref.put(re)

#  receives status messages from muse_app, including start, stop & pause feedback (tools/osc_scanner/osc_scanner_muse_metrics.py for testing)
def handle_muse_app_message(stream, address, *args):

    # last received time will be used to check if the /muse_metrics stream is still sending packages
    #  if longer than 1s not received -> muse is stoped (check in /eeg stream)
    stream['last_data_received'] = time.time()

    # stop: no /muse_metrics osc steam
    #
    # calibrating:         args[6] == 0       args[23] == 2       args[33] == 0
    # feedgack / rec:      args[6] == 1       args[23] == 2       args[33] == 1
    # pause:               args[6] == -1      args[23] == 3       args[33] == 2
    # setting: continue meditation (after meditationtimer has ended): args[30] == 1, do not continue:  args[30] == 0
    if args[33] == 0:
        stream['pause'] = 0
        stream['calibrate'] = 1
        stream['rec'] = 0
    elif args[33] == 1:
        stream['pause'] = 0
        stream['calibrate'] = 0
        stream['rec'] = 1
    else:
        stream['pause'] = 1
        stream['calibrate'] = 0
        stream['rec'] = 0







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

    # if type == opt[0]:
    #     buffer_ica.put(signal['ica_good'])



def osc_start(data):
    global dispatcher

    dispatcher = dispatcher.Dispatcher()
# muse app osc streams
    #buffer_eeg, buffer_signal, buffer_ica, buffer_drlref,
    dispatcher.map("/eeg", partial(handle_eeg_message, data['buffer']['eeg'], data['buffer']['signal_quality'],
                                   data['buffer']['ica'], data['buffer']['drlref'], data['signal'], data['conf'],
                                   data['stream']))
    # sends status messages from muse app, including start, stop & pause feedback (tools/osc_scanner/osc_scanner_muse_metrics.py for testing)
    dispatcher.map("/muse_metrics", partial(handle_muse_app_message, data['stream'], ))
    if not data['conf']['no_heart_rate_file']:
        dispatcher.map("/ppg", partial(handle_ppg_message, data['buffer']['heart_rate'], data['conf'], data['stream']))
    if not data['conf']['no_acc_file']:
        dispatcher.map("/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf'], data['stream']))
    if not data['conf']['no_ica_file']:
        dispatcher.map("/is_good", partial(handle_ica_message, data['buffer']['ica'], data['signal'], data['stream'], ))
    if not data['conf']['no_signal_quality_file']:
        dispatcher.map("/hsi", partial(handle_electrodeFit_message, data['buffer']['signal_quality'], data['signal'], data['stream'], ))
    if not data['conf']['no_drlref_file']:
        dispatcher.map("/drlref", partial(handle_drlref_message, data['buffer']['drlref'], data['signal'], data['stream'], ))




# mind monitor osc streams
    dispatcher.map("/muse/eeg", partial(handle_eeg_message, data['buffer']['eeg'], data['buffer']['signal_quality'],
                                   data['buffer']['ica'], data['buffer']['drlref'], data['signal'], data['conf'],
                                   data['stream']))  # mind monitor osc
    if not data['conf']['no_acc_file']:
        dispatcher.map("/muse/acc", partial(handle_acc_message, data['buffer']['acc'], data['feedback']['acc'], data['conf'], data['stream']))  # muse app osc
    if not data['conf']['no_signal_quality_file']:
        dispatcher.map("/muse/elements/horseshoe", partial(handle_electrodeFit_message, data['signal'], data['stream'], ))  # mind monitor osc
    # a bit tricky, because mindmonitor splits the ica into 3 parts..
    # if not data['conf']['no_ica_file']:
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

