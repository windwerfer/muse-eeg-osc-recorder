import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np

from lib.feedback_graph import MovingGraph


# Your feedback_acc function remains mostly the same, but ensure it's using this updated calculate_movement

# biofeedback thread
def feedback_acc_start(data):
    
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
