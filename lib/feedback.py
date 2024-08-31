import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np

from lib.feedback_filters import EMAFilter, LowPassFilter
from lib.feedback_graph import MovingGraph

import collections

def feedback_acc_start(data):

    show_graph = False
    if show_graph:
        graph = MovingGraph(ylim=(-1, 1))
    WINDOW_SIZE = 5
    dx_queue = collections.deque(maxlen=WINDOW_SIZE)
    dy_queue = collections.deque(maxlen=WINDOW_SIZE)
    dz_queue = collections.deque(maxlen=WINDOW_SIZE)

    ema_dx = EMAFilter(alpha=0.1)
    ema_dy = EMAFilter(alpha=0.1)
    ema_dz = EMAFilter(alpha=0.1)

    lp_filter = LowPassFilter(cutoff_frequency=0.1, sampling_rate=2)

    # Define a threshold for detecting nods
    NOD_THRESHOLD = 0.5  # Adjust this value based on your data

    while True:
        if data['feedback']['acc']:
            prev_x, prev_y, prev_z = None, None, None
            relative_movements = []

            for acc in data['feedback']['acc']:
                x, y, z = acc['x'], acc['y'], acc['z']

                if prev_x is not None:
                    dx = x - prev_x
                    dy = y - prev_y
                    dz = z - prev_z
                    relative_movements.append({'dx': dx, 'dy': dy, 'dz': dz})
                else:
                    relative_movements.append({'dx': 0, 'dy': 0, 'dz': 0})

                prev_x, prev_y, prev_z = x, y, z

            sum_dx = sum(abs(item['dx']) for item in relative_movements)
            sum_dy = sum(abs(item['dy']) for item in relative_movements)
            sum_dz = sum(abs(item['dz']) for item in relative_movements)

            # dx_queue.append(sum_dx)
            # dy_queue.append(sum_dy)
            # dz_queue.append(sum_dz)

            # avg_dx = sum(dx_queue) / len(dx_queue)
            # avg_dy = sum(dy_queue) / len(dy_queue)
            # avg_dz = sum(dz_queue) / len(dz_queue)
            #
            # filtered_dx = ema_dx.update(sum_dx)
            # filtered_dy = ema_dy.update(sum_dy)
            # filtered_dz = ema_dz.update(sum_dz)

            fv = lp_filter.update([sum_dx, sum_dy, sum_dz])

            data['stats']['nod'] = fv[0] + fv[1] + fv[2]

            # Detect nodding motion
            if (fv[0] + fv[1] + fv[2] ) > 0.2:
                print("Nod detected!")
            #print(filtered_values[1])
            if show_graph:
                graph.update(fv[0], fv[1], fv[2])
                plt.pause(0.001)

            data['feedback']['acc'].clear()
        time.sleep(4)

