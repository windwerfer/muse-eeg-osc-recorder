

import csv
import os

import sys
import time
import zipfile

from queue import Queue



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

        # Retrieve and process all items in the queue
        while not data['buffer'][name].empty():
            b = data['buffer'][name].get()  # Get an item from the queue

            if data['conf']['add_time_column']:
                current_timestamp = last_timestamp[name] + 1 / sr * 1000
                b['timestamp'] = round(current_timestamp, 4)

            data['file']['csv_writer'][name].writerow(b)
            data['file']['open'][name].flush()

            # Mark the task as done
            data['buffer'][name].task_done()

            if data['conf']['add_time_column']:
                last_timestamp[name] = current_timestamp


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

        if not data['buffer']['eeg'].empty():

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


                data['stats']['rec_start_time'] = time.time()

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
            if last_received_time is not None and last_received_time + data['conf']['wait_until_starting_new_recording'] < now:
                try:

                    last_timestamp['eeg'] = 0
                    last_timestamp['heart_rate'] = 0
                    last_timestamp['acc'] = 0
                    last_timestamp['signal_quality'] = 0

                    last_received_time = None

                    close_and_zip_files(data)



                except Exception as e:
                    print(' Warning: recoded file not found.. ')



        #print_stats()
        time.sleep(10)


def count_lines_in_file(filename):
    try:
        with open(filename, 'r') as file:
            # Read all lines and count them
            line_count = sum(1 for line in file)
        return line_count
    except FileNotFoundError:
        print(f"Sorry, the file {filename} does not exist.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

def close_and_zip_files(data):
    

    try:
        for f in data['file']['open']:
            data['file']['open'][f].close()

        #sys.stdout.write(f"\r  files are beeing compressed. please wait a short while..                   ")
        #sys.stdout.flush()
        
        # recording lenght
        # rec_lenght = int( round( (time.time() - data['stats']['rec_start_time']) / 60, 0) )
        lines_in_eeg_csv = count_lines_in_file( f"{data['folder']['out']}/{data['folder']['tmp']}/{data['file']['name']['eeg']}")
        rec_lenght = int( round( lines_in_eeg_csv / data['conf']['sampling_rate']['eeg'] / 60 ) )

        # Create a ZIP file with normal compression
        zip_file_name = f"{data['folder']['tmp']}_{rec_lenght}min.zip"
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

        # make sure all queues are empty
        for b in data['buffer']:
            while not data['buffer'][b].empty():
                x = data['buffer'][b].get()
        for b in data['feedback']:
            while not data['feedback'][b].empty():
                x = data['feedback'][b].get()

        data['stats']['moved'] = 0
        data['stats']['moved_continuous'] = 0
        data['stats']['moved_sum'] = 0
        data['stats']['rec_start_time'] = 999999999999

        sys.stdout.write(f"\r+{zip_file_name} saved.                     \n")
        sys.stdout.flush()
        # print(f'\n  {zip_file_name} saved.')

    except Exception as e:
        print(' Warning: recoded file not found.. \n', e)


def gracefully_end(data):

    data['conf']['exiting'] = True

    sys.stdout.write(f"\r   (please wait.. finishing up)                    \n")
    sys.stdout.flush()
    if data['folder']['tmp'] != '':
        close_and_zip_files(data)

    print('\nprogramm ended. all good.')
    os._exit(0)


