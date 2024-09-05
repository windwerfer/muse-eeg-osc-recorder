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



def reconstruct_eeg_df(cleaned_eeg, original_eeg_df, channel_names=None, sample_rate=256):
    """
    Reconstruct the EEG DataFrame from ICA-cleaned signals.

    Parameters:
    - cleaned_eeg: numpy array, the cleaned EEG signals returned from ICA process
    - original_eeg_df: DataFrame, the original EEG data DataFrame to get time information
    - channel_names: list of str, names for the EEG channels. If None, uses original column names excluding 'time_seconds'.
    - sample_rate: int, the sampling rate of the EEG data in Hz

    Returns:
    - DataFrame: Reconstructed EEG data with time information and specified or original channel names
    """
    if channel_names is None:
        # If no channel names are provided, use all columns from the original data except 'time_seconds'
        channel_names = [col for col in original_eeg_df.columns if col != 'time_seconds']

    # Check if the number of provided channel names matches the number of signals
    if len(channel_names) != cleaned_eeg.shape[1]:
        raise ValueError("The number of channel names must match the number of channels in cleaned_eeg.")

    # Create time series
    time_seconds = original_eeg_df['time_seconds'].values if 'time_seconds' in original_eeg_df else np.arange(len(cleaned_eeg)) / sample_rate

    # Construct the DataFrame
    cleaned_eeg_df = pd.DataFrame(cleaned_eeg, columns=channel_names)
    cleaned_eeg_df['time_seconds'] = time_seconds

    return cleaned_eeg_df

# Usage example:
# Assuming 'cleaned_eeg' is what you returned from your ICA function
# and 'eeg_data' is your original DataFrame

# cleaned_eeg_df = reconstruct_eeg_df(cleaned_eeg, eeg_data)

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    """
    Apply a bandpass filter to the data.

    Parameters:
    - data: numpy array, the EEG data to filter
    - lowcut: float, lower bound of the frequency band
    - highcut: float, upper bound of the frequency band
    - fs: float, sampling frequency of the data
    - order: int, order of the filter

    Returns:
    - y: numpy array, filtered data
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)


def compute_fft(signal, fs):
    """
    Compute the Fast Fourier Transform for the given signal.

    Parameters:
    - signal: numpy array, the signal to transform
    - fs: float, sampling frequency

    Returns:
    - freqs: numpy array, frequencies corresponding to FFT
    - power: numpy array, power spectral density or signal power
    """
    n = len(signal)
    fhat = np.fft.fft(signal, n)
    PSD = fhat * np.conj(fhat) / n
    freqs = np.fft.fftfreq(n, 1/fs)
    idx = np.argsort(freqs)
    return freqs[idx], PSD[idx]


def average_channels(eeg_data, channels_to_average):
    """
    Average the specified channels in the EEG data.

    Parameters:
    - eeg_data: DataFrame, contains the EEG data
    - channels_to_average: list of str, names of the channels to average

    Returns:
    - numpy array, averaged values of the specified channels
    """
    if not set(channels_to_average).issubset(eeg_data.columns):
        raise ValueError("One or more channels specified are not in the dataframe.")

    # Ensure we're not including non-EEG columns like 'time_seconds'
    valid_channels = [ch for ch in channels_to_average if ch in eeg_data.columns and ch != 'time_seconds']

    # Average the channels
    averaged_data = eeg_data[valid_channels].mean(axis=1).values

    return averaged_data


def plot_eeg_bands(eeg_data, fs=256):
    """
    Plot the EEG data in different frequency bands.

    Parameters:
    - eeg_data: DataFrame, contains time and EEG channel data
    - fs: int, sampling frequency in Hz
    """
    bands = {
        'Delta': (0.5, 4),
        'Theta': (4, 8),
        'Alpha': (8, 12),
        'Beta': (12, 30),
        'Gamma': (30, 100)
    }

    average_af = average_channels(eeg_data, ['af7', 'af8'])

    # or if no average is wanted:
    #average_af = eeg_data['tp9'].values

    plt.figure(figsize=(14, 10))
    for i, (band, (low, high)) in enumerate(bands.items(), 1):
        # Assuming 'tp9' is one of your channels, adjust if necessary
        #filtered = bandpass_filter(eeg_data['tp9'].values, low, high, fs)
        filtered = bandpass_filter(average_af, low, high, fs)
        freqs, power = compute_fft(filtered, fs)

        plt.subplot(len(bands), 1, i)
        plt.plot(freqs, np.abs(power))
        plt.xlim([low, high])
        plt.title(f'{band} Band')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power')

    plt.tight_layout()
    plt.show()


def main():
    pass


if __name__ == "__main__":


    eeg_data = load_data('../out_eeg/tho_eeglab_2024.09.02_19.07.zip', load_from=2000, load_until=2400) #, col_separator='\t')
    print('file loaded')

    clean_eeg_data = do_ica(eeg_data)
    print('ica done')



    clean_eeg_data_as_channels = reconstruct_eeg_df(clean_eeg_data, eeg_data)

    #plot_eeg_bands(eeg_data)
    plot_eeg_bands(clean_eeg_data_as_channels)



    main()