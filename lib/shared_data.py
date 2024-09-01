class Shared_Data:
    def __init__(self):
        self._data = {
            'buffer': {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []},
            'feedback': {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []},
            'signal': {'electrode': [4, 4, 4, 4], 'is_good': 0},
            'columns': {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []},
            'conf': {},
            'stats': {'refresh_interval': 0.5, 'cpu': 0, 'cpu_one_core': 0.0, 'nr_cpu_cores': 1, 'battery': None, 'recording': 0,
         'moved': '', 'counter': '-'},
            'file': {'name': {}, 'open': {}, 'csv_writer': {}},
            'folder': {'out': "out_eeg", 'tmp': ''}
        }

        # self._data['buffer'] = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
        # self._data['feedback'] = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
        # self._data['columns'] = {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []}
        # self._data['signal'] = {'electrode': [4, 4, 4, 4], 'is_good': 0}
        # self._data['folder'] = {'out': "out_eeg", 'tmp': ''}
        # self._data['file'] = {'name': {}, 'open': {}, 'csv_writer': {}}


    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        raise KeyError(f"No such dataset: {key}")

    def __setitem__(self, key, value):
        if key in self._data:
            self._data[key] = value
        else:
            l = []
            for a in self._data:
                l.append(a)
            s = ', '.join(l)
            raise KeyError(f"Cannot set {key}. Only {s} are allowed.")
