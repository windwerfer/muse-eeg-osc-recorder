import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from scipy import signal
import re

import zipfile
import io
import math

from scipy.signal import butter, lfilter
from sklearn.decomposition import FastICA


def load_data(filename, keep_channels=['tp9', 'af7', 'af8', 'tp10'], sample_rate=256, load_from=0, load_until=None, max_duration=None, col_separator=','):
    """
    Load EEG data from a CSV file, which might be inside a zip archive. Assumes column order if no header is present.

    Parameters:
    - filename: str, path to the CSV or ZIP file containing the CSV.
    - keep_channels: list of str, names of the channels to keep (must match predefined names if no header).
    - sample_rate: int, the sampling rate of the EEG data in Hz.
    - load_from: float, start loading data from this time in seconds (default 0).
    - load_until: float, stop loading data at this time in seconds (default None, load until end).
    - max_duration: float, maximum duration to load in seconds (overrides load_until if set).

    Returns:
    - eeg_data: DataFrame, contains the time series data for the specified channels within the time range.
    """
    # Define default column names if no header is provided
    default_columns = ['tp9', 'af7', 'af8', 'tp10']


    # Function to check if a line contains letters
    def contains_letters(line):
        return bool(re.search('[a-zA-Z]', line))

    # Determine if the file is a zip or a csv
    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            csv_file_name = [name for name in zip_ref.namelist() if name.endswith('_eeg.csv')][0]
            with zip_ref.open(csv_file_name) as csv_file:
                # Check if the CSV has a header
                first_line = csv_file.readline().decode('utf-8').strip()
                csv_file.seek(0)  # Reset file pointer to the start
                has_header = contains_letters(first_line)

                if has_header:
                    eeg_df = pd.read_csv(io.TextIOWrapper(csv_file), sep=col_separator)
                else:
                    eeg_df = pd.read_csv(io.TextIOWrapper(csv_file), sep=col_separator, header=None, names=default_columns)
    else:
        # Check if the CSV file has a header
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
        has_header = contains_letters(first_line)

        if has_header:
            eeg_df = pd.read_csv(filename, sep=col_separator)
        else:
            eeg_df = pd.read_csv(filename, sep=col_separator, header=None, names=default_columns)

    # Calculate sample indices based on time parameters
    start_sample = math.floor(load_from * sample_rate)
    if max_duration is not None:
        end_sample = start_sample + math.floor(max_duration * sample_rate)
    elif load_until is not None:
        end_sample = math.floor(load_until * sample_rate)
    else:
        end_sample = None

    # Slice the dataframe based on calculated samples
    eeg_df = eeg_df.iloc[start_sample:end_sample]

    # Add sample number and convert to time in seconds
    eeg_df['sample_number'] = range(start_sample, start_sample + len(eeg_df))
    eeg_df['time_seconds'] = eeg_df['sample_number'] / sample_rate

    # Ensure keep_channels are valid
    valid_channels = [channel for channel in keep_channels if channel in eeg_df.columns]
    if not valid_channels:
        raise ValueError("None of the keep_channels are recognized or present in the data.")

    # Select only the channels we want to keep
    eeg_data = eeg_df[valid_channels + ['time_seconds']].copy()

    return eeg_data

def load_signal_quality(filename, sample_rate=256, load_from=0, load_until=None, max_duration=None, col_separator=','):
    """
    Load signal quality data from a CSV file, which might be inside a zip archive.

    Parameters:
    - filename: str, path to the CSV or ZIP file containing the CSV.
    - sample_rate: int, the sampling rate of the data in Hz.
    - load_from: float, start loading data from this time in seconds (default 0).
    - load_until: float, stop loading data at this time in seconds (default None, load until end).
    - max_duration: float, maximum duration to load in seconds (overrides load_until if set).

    Returns:
    - signal_quality_data: DataFrame, contains the signal quality data within the time range.
    """
    # Define default column names for signal quality data
    default_columns = ['signal_is_good', 'signal_quality_tp9', 'signal_quality_af7', 'signal_quality_af8', 'signal_quality_tp10']

    # Function to check if a line contains letters
    def contains_letters(line):
        return bool(re.search('[a-zA-Z]', line))

    # Determine if the file is a zip or a csv
    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            csv_file_name = [name for name in zip_ref.namelist() if name.endswith('_signal_quality.csv')][0]
            with zip_ref.open(csv_file_name) as csv_file:
                # Check if the CSV has a header
                first_line = csv_file.readline().decode('utf-8').strip()
                csv_file.seek(0)  # Reset file pointer to the start
                has_header = contains_letters(first_line)

                if has_header:
                    signal_quality_df = pd.read_csv(io.TextIOWrapper(csv_file), sep=col_separator)
                else:
                    signal_quality_df = pd.read_csv(io.TextIOWrapper(csv_file), sep=col_separator, header=None, names=default_columns)
    else:
        # Check if the CSV file has a header
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
        has_header = contains_letters(first_line)

        if has_header:
            signal_quality_df = pd.read_csv(filename, sep=col_separator)
        else:
            signal_quality_df = pd.read_csv(filename, sep=col_separator, header=None, names=default_columns)

    # Calculate sample indices based on time parameters
    start_sample = math.floor(load_from * sample_rate)
    if max_duration is not None:
        end_sample = start_sample + math.floor(max_duration * sample_rate)
    elif load_until is not None:
        end_sample = math.floor(load_until * sample_rate)
    else:
        end_sample = None

    # Slice the dataframe based on calculated samples
    signal_quality_df = signal_quality_df.iloc[start_sample:end_sample]

    # Add sample number and convert to time in seconds
    signal_quality_df['sample_number'] = range(start_sample, start_sample + len(signal_quality_df))
    signal_quality_df['time_seconds'] = signal_quality_df['sample_number'] / sample_rate

    return signal_quality_df


def signal_quality_statistics(signal_quality_data, ignored_electrodes=None):
    """
    Calculate statistics for signal quality data, considering ignored electrodes.

    Parameters:
    - signal_quality_data: DataFrame, the signal quality data.
    - ignored_electrodes: list of str, electrodes to ignore in the analysis.

    Returns:
    - stats_df: DataFrame, statistics for non-ignored electrodes.
    - stats_df_bad_electrodes: DataFrame, statistics for ignored electrodes.
    """
    if ignored_electrodes is None:
        ignored_electrodes = []

    # Initialize results dictionaries
    result = {}
    bad_result = {}
    electrodes = ['tp9', 'af7', 'af8', 'tp10']

    for electrode in electrodes:
        # Extract signal quality for the electrode
        signal_quality = signal_quality_data[f'signal_quality_{electrode}']

        # Count non-good signals
        non_good_signals = (signal_quality != 1).sum()

        # Detect blocks of non-good signals
        blocks = (signal_quality != 1).astype(int).groupby(signal_quality.ne(signal_quality.shift()).cumsum()).sum()
        non_good_blocks = blocks[blocks > 0]
        total_non_good_blocks = len(non_good_blocks)
        average_block_length = non_good_blocks.mean() if total_non_good_blocks > 0 else 0

        # Calculate percentages
        total_signals = len(signal_quality)
        good_percentage = 100 * (total_signals - non_good_signals) / total_signals
        non_good_percentage = 100 - good_percentage

        # Store results in the appropriate dictionary
        if electrode in ignored_electrodes:
            bad_result[electrode] = {
                'Non-Good Signals': non_good_signals,
                'Average Block Length': average_block_length,
                'Good Percentage': good_percentage,
                'Non-Good Percentage': non_good_percentage
            }
        else:
            result[electrode] = {
                'Non-Good Signals': non_good_signals,
                'Average Block Length': average_block_length,
                'Good Percentage': good_percentage,
                'Non-Good Percentage': non_good_percentage
            }

    # Convert results to DataFrames and transpose for better representation
    stats_df = pd.DataFrame(result).T
    stats_df_bad_electrodes = pd.DataFrame(bad_result).T

    # Set pandas display options to show all columns
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    return stats_df, stats_df_bad_electrodes



def identify_bad_electrodes(signal_quality_data, threshold=90):
    """
    Identify electrodes with more than a specified percentage of non-good signals.

    Parameters:
    - signal_quality_data: DataFrame, the signal quality data.
    - threshold: float, the percentage threshold above which an electrode is considered bad.

    Returns:
    - ignored_electrodes: list of str, names of electrodes to ignore.
    """
    electrodes = ['tp9', 'af7', 'af8', 'tp10']
    ignored_electrodes = []

    for electrode in electrodes:
        signal_quality = signal_quality_data[f'signal_quality_{electrode}']
        non_good_percentage = (signal_quality > 1).mean() * 100

        if non_good_percentage > threshold:
            ignored_electrodes.append(electrode)

    return ignored_electrodes

def remove_non_connected_electrode_parts(eeg_data, signal_quality_data, ignored_electrodes=None, truncate_only_beginning_and_end=True, sample_frequency_data=256, sample_frequency_signal_quality=256):
    """
    Remove parts of the EEG data where the electrodes were not connected and return both EEG and signal quality data.

    Parameters:
    - eeg_data: DataFrame, the EEG data.
    - signal_quality_data: DataFrame, the signal quality data.
    - ignored_electrodes: list of str, electrodes to ignore in the analysis.
    - truncate_only_beginning_and_end: bool, if True, only truncate non-connected parts at the beginning and end.
    - sample_frequency_data: int, the sampling frequency of the EEG data.
    - sample_frequency_signal_quality: int, the sampling frequency of the signal quality data.

    Returns:
    - eeg_data_filtered: DataFrame, the EEG data with non-connected parts removed.
    - signal_quality_data_filtered: DataFrame, the signal quality data corresponding to the filtered EEG data.
    """
    if ignored_electrodes is None:
        ignored_electrodes = []

    # Resample signal quality data if frequencies do not match
    if sample_frequency_data != sample_frequency_signal_quality:
        signal_quality_data = signal_quality_data.set_index('time_seconds').resample(f'{1/sample_frequency_data}S').ffill().reset_index()

    # Merge EEG data with signal quality data
    merged_data = pd.merge_asof(eeg_data.sort_values('time_seconds'),
                                signal_quality_data.sort_values('time_seconds'),
                                on='time_seconds',
                                direction='nearest')

    # Identify non-connected parts for each electrode
    electrodes = [electrode for electrode in ['tp9', 'af7', 'af8', 'tp10'] if electrode not in ignored_electrodes]
    non_connected = merged_data[[f'signal_quality_{electrode}' for electrode in electrodes]].gt(1).any(axis=1)

    if truncate_only_beginning_and_end:
        # Find the first and last good signal
        first_good_index = non_connected.idxmin()
        last_good_index = non_connected[::-1].idxmin() + 1

        # Ensure valid indices
        if first_good_index >= last_good_index:
            return pd.DataFrame(columns=eeg_data.columns), pd.DataFrame(columns=signal_quality_data.columns)

        # Truncate data
        eeg_data_filtered = merged_data.iloc[first_good_index:last_good_index].copy()
    else:
        # Remove all non-connected parts
        eeg_data_filtered = merged_data[~non_connected].copy()

    # Separate EEG data and signal quality data
    signal_quality_columns = [col for col in merged_data.columns if 'signal_quality' in col]
    signal_quality_data_filtered = eeg_data_filtered[signal_quality_columns + ['time_seconds']].copy()
    eeg_data_filtered.drop(columns=signal_quality_columns, inplace=True)

    return eeg_data_filtered, signal_quality_data_filtered





def main():
    pass


if __name__ == "__main__":

    #todo: warning if eeg_data is empty (file shorter than load_from)
    eeg_data = load_data('../out_eeg/tho_eeglab_2024.09.04_22.02.zip', load_from=0, load_until=60) #, col_separator='\t')
    print('eeg loaded')

    signal_quality_data = load_signal_quality('../out_eeg/tho_eeglab_2024.09.04_22.02.zip', load_from=0, load_until=60) #, col_separator='\t')
    print('signal quality loaded')

    # Identify bad electrodes
    ignored_electrodes = identify_bad_electrodes(signal_quality_data)

    eeg_data_trunc, signal_quality_data_trunc  = remove_non_connected_electrode_parts(eeg_data, signal_quality_data, ignored_electrodes)

    statis_good_el, statis_bad_el = signal_quality_statistics(signal_quality_data, ignored_electrodes)
    signal_quality_statis_trunc = signal_quality_statistics(signal_quality_data_trunc)

    print(statis_good_el)
    print(statis_bad_el)



