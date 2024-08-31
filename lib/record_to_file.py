

import csv
import os

import sys
import time
import zipfile




last_timestamp = {'eeg': 0, 'heart_rate': 0, 'acc': 0, 'signal_quality': 0}

def open_file(name, data, csv_delimiter=','):

    data['file']['open'][name] = open(f"{data['folder']['out']}/{data['folder']['tmp']}/{data['file']['name'][name]}", "w", newline="")
    data['file']['csv_writer'][name] = csv.DictWriter(data['file']['open'][name], fieldnames=data['columns'][name], delimiter=csv_delimiter)
    if data['conf']['add_header_row']:
        data['file']['csv_writer'][name].writeheader()



def write_to_file(name, data):

    current_timestamp = 0

    try:

        sr = data['conf']['sampling_rate'][name]

        for i, b in enumerate(data['buffer'][name]):
            if data['conf']['add_time_column']:
                current_timestamp = last_timestamp[name] + i / sr * 1000
                b['timestamp'] = round(current_timestamp, 4)
            data['file']['csv_writer'][name].writerow(b)
            data['file']['open'][name].flush()

        if data['conf']['add_time_column']:
            last_timestamp[name] = current_timestamp + (1 / sr * 1000)

        data['buffer'][name].clear()
    except Exception as e:
        if data['conf']['exiting'] != True:
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
def process_buffers(data):

    time.sleep(1)

    last_received_time = None


    if data['conf']['use_tabseparator_for_csv']:
        csv_delimiter = '\t'
    else:
        csv_delimiter = ','

    while True:
        # print(heart_rate)

        now = time.time()
        # print(status_isGood)
        # print(status_electrodeFit)

        if data['buffer']['eeg']:

            if last_received_time is None:
                current_timestamp_str = time.strftime("%Y.%m.%d_%H.%M")
                data['folder']['tmp'] = f"{data['conf']['file_name_prefix']}{current_timestamp_str}"
                data['file']['name']['eeg'] = f"{data['conf']['file_name_prefix']}{current_timestamp_str}_eeg.csv"
                data['file']['name']['heart_rate'] = f"{data['conf']['file_name_prefix']}{current_timestamp_str}_heart_rate.csv"
                data['file']['name']['acc'] = f"{data['conf']['file_name_prefix']}{current_timestamp_str}_accelerator.csv"
                data['file']['name']['signal_quality'] = f"{data['conf']['file_name_prefix']}{current_timestamp_str}_signal_quality.csv"
                create_folder(data['folder']['out'])
                create_folder(f"{data['folder']['out']}/{data['folder']['tmp']}")

                open_file('eeg', data, csv_delimiter=csv_delimiter)

                if data['conf']['add_heart_rate_file']:
                    open_file('heart_rate', data, csv_delimiter=csv_delimiter)

                if data['conf']['add_acc_file']:
                    open_file('acc', data, csv_delimiter=csv_delimiter)

                if data['conf']['add_signal_quality_file']:
                    open_file('signal_quality', data, csv_delimiter=csv_delimiter)

                # print('new file created:')
                # print(f" {data['folder']['tmp']} created")
                sys.stdout.write(f"\r {data['folder']['tmp']} created.                     \n")
                sys.stdout.flush()

            write_to_file('eeg', data)


            if data['conf']['add_heart_rate_file']:
                write_to_file('heart_rate', data)

            if data['conf']['add_acc_file']:
                write_to_file('acc', data)

            if data['conf']['add_signal_quality_file']:
                write_to_file('signal_quality', data)

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


def close_and_zip_files(data):
    

    try:
        for f in data['file']['open']:
            data['file']['open'][f].close()

        sys.stdout.write(f"\r  files are beeing compressed. please wait a short while..                   ")
        sys.stdout.flush()

        # Create a ZIP file with normal compression
        zip_file_name = f"{data['folder']['tmp']}.zip"
        ff = []
        with zipfile.ZipFile(f"{data['folder']['out']}/{zip_file_name}", 'w', zipfile.ZIP_DEFLATED) as zipf:
            # pack all created files that are > 0 Bytes
            for f in data['file']['name']:
                ff.append(f"{data['folder']['out']}/{data['folder']['tmp']}/{data['file']['name'][f]}")
                #print(ff[-1])
                if os.path.getsize(ff[-1]) > 0:
                    zipf.write(ff[-1], arcname=os.path.basename(ff[-1]))

        # Delete the original files
        for f in ff:
            os.remove(f)
        # remove tmp folder
        os.rmdir(f"{data['folder']['out']}/{data['folder']['tmp']}")

        # clear file list and tmp folder name
        for f in data['file']['name']:
            data['file']['name'][f] = ''
        data['folder']['tmp'] = ''

        # clear buffers (in case they where not used completly)
        for b in data['buffer']:
            data['buffer'][b].clear()
        for b in data['feedback']:
            data['feedback'][b].clear()

        sys.stdout.write(f"\r+{zip_file_name} saved.                     \n")
        sys.stdout.flush()
        # print(f'\n  {zip_file_name} saved.')

    except Exception as e:
        print(' Warning: recoded file not found.. \n', e)


def gracefully_end(data):

    data['conf']['exiting'] = True

    if data['folder']['tmp'] != '':
        close_and_zip_files(data)

    print('\nend programm. all good.')
    os._exit(0)


