class Shared_Data:
    def __init__(self):
        self._data = {'eeg': {}, 'acc': {}}

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        raise KeyError(f"No such dataset: {key}")

    def __setitem__(self, key, value):
        if key in ['eeg', 'acc']:
            self._data[key] = value
        else:
            raise KeyError(f"Cannot set {key}. Only 'eeg' and 'acc' are allowed.")
