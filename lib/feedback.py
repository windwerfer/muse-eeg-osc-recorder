import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np

from lib.feedback_filters import EMAFilter, LowPassFilter
from lib.feedback_graph import MovingGraph

import collections

from lib.play_sound import play_sound


def feedback_acc_start(data):

    show_graph = False
    if show_graph:
        graph = MovingGraph(ylim=(-1, 1))
    # To store the history of movements
    movement_history = collections.deque(maxlen=20)  # Adjust the length as needed

    while True:
        if data['feedback']['acc']:
            prev_x, prev_y, prev_z = None, None, None
            current_movement = {'dx': 0, 'dy': 0, 'dz': 0}

            for acc in data['feedback']['acc']:
                x, y, z = acc['x'], acc['y'], acc['z']

                if prev_x is not None:
                    current_movement['dx'] += x - prev_x
                    current_movement['dy'] += y - prev_y
                    current_movement['dz'] += z - prev_z
                prev_x, prev_y, prev_z = x, y, z

            # Add the current movement to history
            movement_history.append(current_movement)
            #print(current_movement)

            # Analyze the movement history for patterns like nodding or shaking
            analyze_movement(movement_history)

            # Clear the data for next iteration
            data['feedback']['acc'].clear()
        time.sleep(0.5)  # Adjust sleep time as necessary


def analyze_movement(history):
    # Parameters for nod detection
    THRESHOLD_MAGNITUDE = 0.1  # Minimum movement to be considered significant
    CONSISTENCY_THRESHOLD = 0.6  # 60% of movements should be in the same direction for a nod

    # Analyze x and y movements for nodding patterns
    for axis in ['dx', 'dy']:
        # Count movements in both directions
        positive_movements = sum(1 for move in history if move[axis] > THRESHOLD_MAGNITUDE)
        negative_movements = sum(1 for move in history if move[axis] < -THRESHOLD_MAGNITUDE)

        total_significant_movements = positive_movements + negative_movements

        # Check if there's a dominant direction, suggesting a nod or shake
        if total_significant_movements > 0:
            direction_ratio = max(positive_movements, negative_movements) / total_significant_movements

            if direction_ratio > CONSISTENCY_THRESHOLD:

                play_sound( "audio/boreal_owl.mp3", background=False)

                # # Determine the type of movement based on which axis and direction is dominant
                # if axis == 'dx' and positive_movements > negative_movements:
                #     print("Forward nod detected!")
                # elif axis == 'dx':
                #     print("Backward nod detected!")
                # elif axis == 'dy' and positive_movements > negative_movements:
                #     print("Right shake detected!")
                # elif axis == 'dy':
                #     print("Left shake detected!")

    # Additional check for circular or more complex movements could be implemented here
    # For instance, checking if movements alternate between axes in a pattern
