import threading
from queue import Queue

class Shared_Data:
    def __init__(self):
        self._data = {
            'buffer': {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'signal_quality': Queue()},
            'feedback': {'eeg': Queue(), 'heart_rate': Queue(), 'acc': Queue(), 'signal_quality': Queue()},
            'signal': {'electrode': [4, 4, 4, 4], 'is_good': 0},
            'columns': {'eeg': [], 'heart_rate': [], 'acc': [], 'signal_quality': []},
            'conf': {},
            'stats': {'refresh_interval': 0.5, 'cpu': 0, 'cpu_one_core': 0.0, 'nr_cpu_cores': 1, 'battery': None, 'recording': 0,
         'moved': '', 'moved_sum': 0, 'counter': '-'},
            'file': {'name': {}, 'open': {}, 'csv_writer': {}},
            'folder': {'out': "out_eeg", 'tmp': ''}
        }
        self._signal_lock = threading.Lock()

    def set_signal_is_good(self, is_good):
        with self._signal_lock:
            self._data['signal']['is_good'] = is_good

    def set_signal_electrode(self, electrode):
        with self._signal_lock:
            self._data['signal']['electrode'] = electrode

