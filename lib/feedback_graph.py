import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation


class MovingGraph:
    def __init__(self, window_size=20, update_interval=500, ylim=(-1, 1)):
        """
        Initialize the MovingGraph object.

        :param window_size: Size of the time window in seconds for which data is displayed.
        :param update_interval: Update interval in milliseconds.
        :param ylim: Tuple for y-axis limits.
        """
        self.window_size = window_size
        self.update_interval = update_interval
        self.ylim = ylim

        # Number of data points based on update interval
        self.num_points = int(window_size * 1000 / update_interval)

        # Initialize data buffer
        self.data_buffer = np.zeros((self.num_points, 3))

        # Setup the plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, self.window_size)
        self.ax.set_ylim(self.ylim)

        # Initialize lines
        self.line_x, = self.ax.plot([], [], label='X axis')
        self.line_y, = self.ax.plot([], [], label='Y axis')
        self.line_z, = self.ax.plot([], [], label='Z axis')
        self.ax.legend()

        # Animation setup
        MAX_FRAMES = 1000
        self.ani = FuncAnimation(self.fig, self._update, init_func=self._init, blit=True, interval=self.update_interval, save_count=MAX_FRAMES)

        plt.show(block=False)  # Non-blocking show

    def _init(self):
        """Initialization function for animation."""
        self.line_x.set_data([], [])
        self.line_y.set_data([], [])
        self.line_z.set_data([], [])
        return self.line_x, self.line_y, self.line_z,

    def _update(self, frame):
        """Update function for animation."""
        time = np.linspace(0, self.window_size, len(self.data_buffer))
        self.line_x.set_data(time, self.data_buffer[:, 0])
        self.line_y.set_data(time, self.data_buffer[:, 1])
        self.line_z.set_data(time, self.data_buffer[:, 2])
        return self.line_x, self.line_y, self.line_z,

    def update(self, x, y, z):
        """
        Update the graph with new x, y, z values.

        :param x: New x-axis value
        :param y: New y-axis value
        :param z: New z-axis value
        """
        # Roll the buffer to make room for new data and add new data
        self.data_buffer = np.roll(self.data_buffer, -1, axis=0)
        self.data_buffer[-1] = [x, y, z]
