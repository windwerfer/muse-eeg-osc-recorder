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

def signal_quality_statistics(signal_quality_data):
    # Initialize results dictionary
    result = {}
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

        # Store results
        result[electrode] = {
            'Non-Good Signals': non_good_signals,
            'Average Block Length': average_block_length,
            'Good Percentage': good_percentage,
            'Non-Good Percentage': non_good_percentage
        }

    # Convert results to DataFrame and transpose for better representation
    stats_df = pd.DataFrame(result).T

    # Set pandas display options to show all columns
    pd.set_option('display.max_columns', None)

    # Set display width to a larger value
    pd.set_option('display.width', 1000)

    # rotate 90 degrees
    stats_df_flip = stats_df.transpose()

    # Transpose the DataFrame to rotate it by 90 degrees
    return stats_df

def do_ica(eeg_data,sample_rate=256):
    # Example data setup (replace this with your actual data loading)
    eeg_data_array = eeg_data.drop('time_seconds', axis=1).values  # Assuming 'time_seconds' is not part of the channels

    # Standardize the data (important for ICA)
    eeg_data_standardized = (eeg_data_array - np.mean(eeg_data_array, axis=0)) / np.std(eeg_data_array, axis=0)

    # Number of components to extract. Often this is set to the number of channels, but can be less for dimensionality reduction
    n_components = eeg_data_standardized.shape[1]  # Number of EEG channels

    # Create and fit ICA model
    ica = FastICA(n_components=n_components, random_state=42)  # You can choose different ICA algorithms or parameters
    components = ica.fit_transform(eeg_data_standardized.T)  # Transpose because FastICA expects components as rows

    # components now holds the independent components in its rows
    # To get back to the "EEG space", you can use:
    mixing_matrix = ica.mixing_
    reconstructed_signals = np.dot(components, mixing_matrix.T) + ica.mean_.T

    # Plotting example for one component to visualize
    # plt.figure()
    # plt.plot(components[0, :])  # Plotting the first independent component
    # plt.title('First Independent Component')
    # plt.show()

    # If you want to remove a component (e.g., an artifact), you would zero out its row in 'components'
    # then reconstruct without it. Here's a simple example where we remove the first component:
    components_cleaned = components.copy()
    components_cleaned[0, :] = 0  # Zero out the first component, assuming it's an artifact

    # Reconstruct the signal without the first component
    cleaned_eeg = np.dot(components_cleaned, mixing_matrix.T) + ica.mean_.T



    return cleaned_eeg





def main():
    pass


if __name__ == "__main__":

    #todo: warning if eeg_data is empty (file shorter than load_from)
    eeg_data = load_data('../out_eeg/tho_eeglab_2024.09.04_22.02.zip', load_from=0, load_until=60) #, col_separator='\t')
    print('eeg loaded')

    signal_quality_data = load_signal_quality('../out_eeg/tho_eeglab_2024.09.04_22.02.zip', load_from=0, load_until=60) #, col_separator='\t')
    print('signal quality loaded')

    signal_quality_statis = signal_quality_statistics(signal_quality_data)
    print(signal_quality_statis)

    #clean_eeg_data = do_ica(eeg_data)
    print('ica done')



    main()