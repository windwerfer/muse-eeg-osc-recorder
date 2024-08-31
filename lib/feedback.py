import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np

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
        self.ani = FuncAnimation(self.fig, self._update, init_func=self._init, blit=True, interval=self.update_interval)

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


# Your feedback_acc function remains mostly the same, but ensure it's using this updated calculate_movement

# biofeedback thread
def feedback_acc(data):
    
    # time.sleep(2)

    graph = MovingGraph(ylim=(-0.05, 0.05))

    while True:

        if data['feedback']['acc']:
            # Initialize previous values with None or some initial values
            prev_x, prev_y, prev_z = None, None, None

            # List to store relative movements
            relative_movements = []


            for acc in data['feedback']['acc']:
                # Extract x, y, z from the dictionary
                x, y, z = acc['x'], acc['y'], acc['z']

                # Calculate relative movement
                if prev_x is not None:
                    # Calculate the difference from the previous reading
                    dx = x - prev_x
                    dy = y - prev_y
                    dz = z - prev_z

                    # Store the relative movement
                    relative_movements.append({'dx': dx, 'dy': dy, 'dz': dz})
                else:
                    # For the first iteration, we can't calculate a difference, so we might
                    # choose to either skip this, set to zero, or use the current values directly
                    # Here, setting to zero for consistency with no movement concept:
                    relative_movements.append({'dx': 0, 'dy': 0, 'dz': 0})

                # Update previous values for next iteration
                prev_x, prev_y, prev_z = x, y, z

            # Summing up all relative movements
            sum_dx = sum(abs(item['dx']) for item in relative_movements)
            sum_dy = sum(abs(item['dy']) for item in relative_movements)
            sum_dz = sum(abs(item['dz']) for item in relative_movements)

            # Calculating the average
            # First, check if relative_movements is not empty to avoid division by zero
            if relative_movements:
                count = len(relative_movements)
                avg_dx = sum_dx / count
                avg_dy = sum_dy / count
                avg_dz = sum_dz / count
            else:
                avg_dx, avg_dy, avg_dz = 0, 0, 0

                # After processing all data, get the total movement

            #if signal['is_good']:

            # sys.stdout.write(f"\r{avg_dx:18.16f}   {avg_dy:18.16f}    {avg_dz:18.16f}            \n")
            # sys.stdout.flush()

            graph.update(avg_dx, avg_dy, avg_dz)
            plt.pause(0.001)  # Allow plot to update

            data['feedback']['acc'].clear()
        time.sleep(.5)
