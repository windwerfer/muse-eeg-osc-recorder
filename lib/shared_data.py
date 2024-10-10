import threading
from queue import Queue

class Shared_Data:
    def __init__(self):
        self._data = {
            'buffer': {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'ica': Queue(), 'signal_quality': Queue(), 'drlref': Queue()},
            'feedback': {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'ica': Queue(), 'signal_quality': Queue(), 'drlref': Queue()},
            'signal': {'electrode': [4, 4, 4, 4], 'ica_good': 0, 'ok': 0, 'blink':0, 'jaw_clench':0, 'touching_forehead':0, 'drlref':[0,0] },
            'stream': {'from_muse_app': 0, 'from_mindmonitor_app': 0, 'last_data_received': 0, 'pause': 0, 'stop': 1, 'calibrate': 0, 'rec':0 },
            'columns': {'eeg': [], 'heart_rate': [], 'acc': [], 'ica': [], 'signal_quality': [], 'drlref': []},
            'conf': {},
            'stats': {'refresh_interval': 1, 'cpu': 0, 'cpu_one_core': 0.0, 'nr_cpu_cores': 1, 'battery': None,
                'moved': '', 'moved_sum': 0, 'moved_continuous': 0, 'counter': '-',  'recording': 0,
                'rec_start_time':999999999999, 'pause': False },
            'file': {'name': {}, 'open': {}, 'csv_writer': {}, 'packing': False},
            'folder': {'out': "out_eeg", 'tmp': '', 'note': []}
        }
        self._lock = threading.RLock()


    # the following for
    def __getitem__(self, key):
        with self._lock:
            if key in self._data:
                return self._data[key]

    def __setitem__(self, key, value):
        with self._lock:
            if key in self._data:
                self._data[key] = value
            else:
                raise KeyError(f"Cannot set {key}. Only {', '.join(self._data.keys())} are allowed.")

    def append(self, key, value):
        with self._lock:
            if key not in self._data:
                raise KeyError(f"No such dataset: {key}")
            self._data[key].append(value)

    def clear(self, key):
        with self._lock:
            if key in self._data:
                self._data[key].clear()
            else:
                raise KeyError(f"No such dataset: {key}")

    def set_value(self, key, value):
        with self._lock:
            if key in self._data:
                self._data[key] = value
            else:
                raise KeyError(f"Cannot set {key}. Only {', '.join(self._data.keys())} are allowed.")
