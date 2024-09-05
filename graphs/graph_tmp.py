import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import butter, lfilter


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

if __name__ == "__main__":


    #clean_eeg_data = do_ica(eeg_data)
    print('ica done')

    #clean_eeg_data_as_channels = reconstruct_eeg_df(clean_eeg_data, eeg_data)

    # plot_eeg_bands(eeg_data)
    #plot_eeg_bands(clean_eeg_data_as_channels)