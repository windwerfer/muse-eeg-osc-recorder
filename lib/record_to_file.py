

import csv
import os
import sys
import time
import zipfile

from write_osc_to_files import buffered_data
from write_osc_to_files import buffered_feedback


folder = {'out' : "out_eeg", 'tmp': ''}
file = {'name':{}, 'open':{}, 'csv_writer': {} }

last_timestamp = {'eeg': 0, 'heart_rate': 0, 'acc': 0, 'signal_quality': 0}

def open_file(name, csv_delimiter=','):
    global file, folder, conf

    file['open'][name] = open(f"{folder['out']}/{folder['tmp']}/{file['name'][name]}", "w", newline="")
    file['csv_writer'][name] = csv.DictWriter(file['open'][name], fieldnames=columns[name], delimiter=csv_delimiter)
    if conf['add_header_row']:
        file['csv_writer'][name].writeheader()



def write_to_file(name):
    global last_timestamp, file, conf

    current_timestamp = 0

    try:

        sr = conf['sampling_rate'][name]

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
    global columns, conf, file, folder, last_timestamp

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


