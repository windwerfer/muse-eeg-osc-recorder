import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import numpy as np

from lib.feedback_filters import EMAFilter, LowPassFilter
from lib.feedback_graph import MovingGraph

import collections

from lib.play_sound_termux import play_sound


def feedback_acc_start(data):

    show_graph = False
    if show_graph:
        graph = MovingGraph(ylim=(-1, 1))
    # To store the history of movements
    movement_history = collections.deque(maxlen=data['conf']['nod_length'])  # Adjust the length as needed

    last_play_time = 0  # Timestamp of the last time play_sound was called
    cooldown = 60  # Cooldown period in seconds
    cooldown_nod = 120  # Cooldown period in seconds

    # start_time = time.time()
    begin_after = 60   #minimum time before play in s



    while True:

        if not data['feedback']['acc'].empty():
            prev_x, prev_y, prev_z = None, None, None
            current_movement = {'dx': 0, 'dy': 0, 'dz': 0}

            # Retrieve and process all items in the queue
            while not data['feedback']['acc'].empty():
                acc = data['feedback']['acc'].get()  # Get and remove an item from the queue
                x, y, z = acc['x'], acc['y'], acc['z']

                if prev_x is not None:
                    current_movement['dx'] += x - prev_x
                    current_movement['dy'] += y - prev_y
                    current_movement['dz'] += z - prev_z
                prev_x, prev_y, prev_z = x, y, z

            # Add the current movement to history
            movement_history.append(current_movement)
            # print(current_movement)

            # Analyze the movement history for patterns like nodding or shaking
            moved = analyze_movement(movement_history, data['conf']['nod_threshold_magnitude'])
            current_time = time.time()

            if moved > 0 and current_time > data['stats']['rec_start_time'] + begin_after:

                play = ''
                vol = 100

                if current_time - last_play_time >= cooldown:

                    data['stats']['moved_sum'] += 1

                    if data['stats']['moved_continuous'] == 5:
                        play = "audio/biohazard-alarm.mp3"
                        vol = 30
                    elif data['stats']['moved_continuous'] == 6:
                        play = "audio/biohazard-alarm.mp3"
                        vol = 60
                    elif data['stats']['moved_continuous'] > 6:
                        play = "audio/biohazard-alarm.mp3"
                        vol = 100
                    else:
                        play = 'audio/wolf.mp3'
                    last_play_time = current_time

                    if current_time - last_play_time <= cooldown_nod:
                        data['stats']['moved_continuous'] += 1

                if play != '':
                    play_sound(play, volume=vol, background=False)  # boreal_owl.mp3

            else:
                if current_time >= last_play_time + cooldown_nod:
                    data['stats']['moved_continuous'] = 0
                    pass



            #data['stats']['moved'] = f"{moved}"

        time.sleep(0.5)  # Adjust sleep time as necessary


def analyze_movement(history, nod_threshold_magnitude):
    # Parameters for nod detection 
    # nod_threshold_magnitude: 0.8 seems best for me (very sensitiv), 0.09 probably good for people who move more like kRob,  1.0 relaxed
    # x+y was also good..
    THRESHOLD_MAGNITUDE = nod_threshold_magnitude  # Minimum movement to be considered significant
    CONSISTENCY_THRESHOLD = 0.6  # 60% of movements should be in the same direction for a nod

    moved = {'dx':0,'dy':0,'dz':0}

    # Analyze x and y movements for nodding patterns
    for axis in ['dx', 'dy', 'dz']:
        # Count movements in both directions
        positive_movements = sum(1 for move in history if move[axis] > THRESHOLD_MAGNITUDE)
        negative_movements = sum(1 for move in history if move[axis] < -THRESHOLD_MAGNITUDE)

        total_significant_movements = positive_movements + negative_movements

        # Check if there's a dominant direction, suggesting a nod or shake
        if total_significant_movements > 0:
            direction_ratio = max(positive_movements, negative_movements) / total_significant_movements

            if direction_ratio > CONSISTENCY_THRESHOLD:

               return True

                # # Determine the type of movement based on which axis and direction is dominant
                # if axis == 'dx' and positive_movements > negative_movements:
                #     print("Forward nod detected!")
                # elif axis == 'dx':
                #     print("Backward nod detected!")
                # elif axis == 'dy' and positive_movements > negative_movements:
                #     print("Right shake detected!")
                # elif axis == 'dy':
                #     print("Left shake detected!")

    return False
    # Additional check for circular or more complex movements could be implemented here
    # For instance, checking if movements alternate between axes in a pattern
