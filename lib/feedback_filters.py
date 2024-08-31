import numpy as np


class EMAFilter:
    def __init__(self, alpha):
        self.alpha = alpha  # The smoothing factor, between 0 and 1. A higher alpha discounts older observations faster.
        self.value = None

    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value


class LowPassFilter:
    def __init__(self, cutoff_frequency, sampling_rate):
        self.cutoff = cutoff_frequency
        self.rate = sampling_rate
        self.prev_values = None

    def update(self, new_values):
        if self.prev_values is None:
            self.prev_values = np.array(new_values)
            return np.abs(new_values).tolist()  # Return absolute values of the input for the first iteration

        # Calculate filter coefficients
        b0 = (2 * np.pi * self.cutoff) / (self.rate + 2 * np.pi * self.cutoff)
        a1 = (self.rate - 2 * np.pi * self.cutoff) / (self.rate + 2 * np.pi * self.cutoff)

        # Apply the filter to each dimension
        filtered_values = b0 * np.array(new_values) + (b0 * self.prev_values - a1 * self.prev_values)

        # Update previous values for next iteration
        self.prev_values = np.array(new_values)

        # Return absolute values of the filtered results
        return np.abs(filtered_values).tolist()