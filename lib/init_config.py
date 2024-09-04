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
    parser.add_argument('--add_heart_rate_file', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add separate file for heart rate.')
    parser.add_argument('--add_acc_file', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add separete file for accelaration (gryoscope) value.')
    parser.add_argument('--add_signal_quality_file', type=bool, default=True, choices=[0, 1],
                        help='Default: 1. Add signal quality file. each row corresponds to the same row in the eeg file. they are separate to keep the fileformat compatable with eeglab.')
    parser.add_argument('--add_signal_quality_for_each_electrode', type=bool, default=True, choices=[0, 1],
                        help='Default 1. Add signal quality column for each electrode.')
    parser.add_argument('--add_aux_columns', action='store_true',
                        help='Add auxiliary signal columns (aux0 and aux1) for recording eeg signals. Default: disabled because you need to connect a external electrode to the muse (most people dont use it).')
    parser.add_argument('--add_time_column', action='store_true',
                        help='Add a time column to the signal recording. Default: disabled because most programms expect a fixed amount of signals per second (eg 256 for the muse).')
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

    return parser.parse_args()


def init_conf(data):
    # Parse command-line arguments

    args = parse_arguments()

    # Create a configuration dictionary with the parsed arguments
    data['conf'] = {
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

    if data['conf']['add_time_column']:
        data['columns']['eeg'].append('timestamp')
        data['columns']['heart_rate'].append('timestamp')
        data['columns']['acc'].append('timestamp')
        data['columns']['signal_quality'].append('timestamp')


    # Define the CSV column names based on OSC addresses
    data['columns']['eeg'].extend(["tp9", "af7", "af8", "tp10"])
    #data['columns']['heart_rate'].extend(["heart_rate_0", "heart_rate_1", "heart_rate_2"])
    data['columns']['heart_rate'].extend(["heart_rate_1"]) # muse only uses heart rate sensor 1, sensor 0 & 2 (infrared and green) are not used, mind monitor does not send the heartrate at all
    data['columns']['acc'].extend(["x", "y", "z"])
    data['columns']['signal_quality'].extend(["all_signals_are_good"])

    if data['conf']['add_aux_columns']:
        data['columns']['eeg'].extend(['aux0', 'aux1'])

    if data['conf']['add_signal_quality_for_each_electrode']:
        data['columns']['signal_quality'].extend(['signal_quality_TP9', 'signal_quality_AF7', 'signal_quality_AF8', 'signal_quality_TP10'])



    data['conf']['exiting'] = False # marker for threads that the programm is exiting

    # muse s and muse 2 have the same specs for eeg, ppg (heart_rate), and acc (gryoscope)
    #  (signal_quality has the same sampling rate as eeg)
    data['conf']['sampling_rate'] = {'eeg': 256, 'signal_quality': 256, 'heart_rate': 64, 'acc': 52}



