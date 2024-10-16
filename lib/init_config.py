import argparse



def parse_arguments():
    parser = argparse.ArgumentParser(description='Configure EEG recording parameters.')

    # Define command-line arguments for each configuration parameter
    # parser.add_argument('--only_record_if_signal_is_good', action='store_false',
    # parser.add_argument('--only_record_if_signal_is_good', type=bool, default=True,
    parser.add_argument('--only_record_if_signal_is_good', action='store_true',
                        help='Default disabled. Record osc only if all sensors have good signal quality.')
    parser.add_argument('--if_signal_is_not_good_set_signal_to', type=str, default='record_received_signal',
                        choices=['NaN', '0.0', 'record_received_signal'],
                        help='Default "record_received_signal". The Muse device has a Signal Quality marker, that will be 0 if the Signal is bad/not received correctly. set to "record_received_signal" to handle afterwards (most flexible). Substitue with this value (NaN = no data received marker, 0.0 = blank value), but you might lose contextual information. "record_received_signal" will save the received value, even though it is most likely an artifact, needs more processing after recording.')
    parser.add_argument('--no_heart_rate_file', action='store_true',
                        help='Disables heart rate file (ppg sensor).')
    parser.add_argument('--no_acc_file', action='store_true',
                        help='Disables accelerator (gryoscope) file.')
    parser.add_argument('--no_signal_quality_file', action='store_true',
                        help='Disables Signal Quality file. (tp9,af7,af8,tp10 sensors). 1 = good connection, 2 = mediocre connection, 4 = poor connection. same row count as the eeg signal.')
    parser.add_argument('--no_ica_file', action='store_true',
                        help='Disables ICA file. 1 = signal is without artifacts, 0 = artifacts (blink, muscle contract). same row count as the eeg signal, but is 1s behind the eeg signal. eg: line 456 of the eeg file corresbonds to line 200 of the ica file.')
    parser.add_argument('--no_drlref_file', action='store_true',
                        help='Disables file for Muse DRL and REF sensors. The units of both values are in microvolts. (used as reference electrodes to see incongruities between sensors)')
    parser.add_argument('--add_aux_columns', action='store_true',
                        help='Add auxiliary signal columns (aux0 and aux1) for recording eeg signals. Default: disabled because you need to connect a external electrode to the muse (most people dont use it).')
    parser.add_argument('--use_tabseparator_for_csv', action='store_true',
                        help='Use tab as separator in CSV. Default is comma separator.')
    parser.add_argument('--add_header_row', action='store_true',
                        help='Add header row (eg tp9,af7,af8,tp10 for the eeg data). Default disabled because EegLab doesnt accept a header row.')
    parser.add_argument('--port', type=int, default=5000,
                        help='Default 5000. Port number for the server.')
    parser.add_argument('--ip', type=str, default='0.0.0.0',
                        help='Default "0.0.0.0". IP address for the server to listen to. "0.0.0.0" listens to all ip addresses.')
    parser.add_argument('--file_name_prefix', type=str, default='eeg_',
                        help='Default "eeg_". File name prefix for output files.')
    parser.add_argument('--feedback_acc', action='store_true',
                        help='Use the Accelerometer data to find sleepiness. Default: disabled')
    parser.add_argument('--wait_before_starting_new_rec', type=int, default=15,
                        help='Default 15. Time in seconds to wait when the osc stream stopped until closing the file and starting a new one.')
    parser.add_argument('--graphs_folder', type=str, default='cache',
                        help='folder where the generated images are stored and the http server is started in. defautl: cache')

    return parser.parse_args()


def init_conf(data):
    # Parse command-line arguments

    args = parse_arguments()

    # Create a configuration dictionary with the parsed arguments
    data['conf'] = {
        'only_record_if_signal_is_good': args.only_record_if_signal_is_good,
        'if_signal_is_not_good_set_signal_to': args.if_signal_is_not_good_set_signal_to,
        'no_heart_rate_file': args.no_heart_rate_file,
        'no_acc_file': args.no_acc_file,
        'no_signal_quality_file': args.no_signal_quality_file,
        'no_ica_file': args.no_ica_file,
        'no_drlref_file': args.no_drlref_file,
        'add_aux_columns': args.add_aux_columns,
        'use_tabseparator_for_csv': args.use_tabseparator_for_csv,
        # 'add_time_column': args.add_time_column,
        'add_header_row': args.add_header_row,
        'port': args.port,
        'ip': args.ip,
        'file_name_prefix': args.file_name_prefix,
        'feedback_acc': args.feedback_acc,
        'wait_before_starting_new_rec': args.wait_before_starting_new_rec,
        'graphs_folder': args.graphs_folder,
    }


    # Define the CSV column names based on OSC addresses
    data['columns']['eeg'].extend(["tp9", "af7", "af8", "tp10"])
    data['columns']['heart_rate'].extend(["heart_rate_1"]) # muse only uses heart rate sensor 1, sensor 0 & 2 (infrared and green) are not used, mind monitor does not send the heartrate at all
    data['columns']['acc'].extend(["x", "y", "z"])
    data['columns']['ica'].extend(["ica"])
    data['columns']['signal_quality'].extend(['tp9', 'af7', 'af8', 'tp10'])
    data['columns']['drlref'].extend(["drl","ref"])

    if data['conf']['add_aux_columns']:
        data['columns']['eeg'].extend(['aux0', 'aux1'])




    data['conf']['exiting'] = False # marker for threads that the programm is exiting

    # muse s and muse 2 have the same specs for eeg, ppg (heart_rate), and acc (gryoscope)
    #  (signal_quality has the same sampling rate as eeg)
    data['conf']['sampling_rate'] = {'eeg': 256, 'heart_rate': 64, 'acc': 52, 'signal_quality':256, 'ica': 10, 'drlref':256}


    # nod_threshold_magnitude: how sensitive the nodding recognition is.
    # good values are between 0.10 and 0.08 (0.08 beeing more sensitive and 0.10 less so)
    # 0.08 seems best for me (very sensitiv), 0.09 probably good for people who move more like kRob,  1.0 relaxed
    # 0.07 = 2cm nods recognised - very sensitive but works well
    data['conf']['nod_threshold_magnitude'] = 0.07
    # how slow do you nodd? each increase in number adds 0.5s to the recognised nod length (20 -> 10s nod is recognised)
    data['conf']['nod_length'] = 20

    # the time the script waits while no osc data arrives, before assuming its a new recording session and starts a new file
    # data['conf']['wait_before_starting_new_rec'] = 15        # now set through arg parse


