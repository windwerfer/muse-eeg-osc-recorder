from pythonosc import dispatcher
from pythonosc import osc_server

import os
import time


def is_int2(i):
    try:
    # Attempt to convert i to an integer
        int_value = int(i)
    # If conversion succeeds, i represents an integer
        return True
    except ValueError:
    # If conversion fails, i is not an integer string
        return False

def is_int(i):
    if isinstance(i, int):
        return True
    elif isinstance(i, float):
        # Check if the float has no decimal part or it's effectively zero
        return i.is_integer()
    elif isinstance(i, str):
        try:
            # Convert string to float first since int() would fail on strings like '3.0'
            float_value = float(i)
            return float_value.is_integer()
        except ValueError:
            return False
    else:
        # If i is neither int, float, nor a string representation of a number, return False
        return False

# Function to clear the screen
def clear_screen():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

list_only_new = False
list_stats = True
adr = []

# Global variables for timing
last_print_time = 0
print_interval = 0.5  # seconds

def print_handler(address, *args):
    global last_print_time, s
    
    if list_only_new:
        if address not in adr:
            adr.append(address)
            print(f"{address}: {args}")
    elif list_stats:
        if address == '/muse_metrics':
            current_time = time.time()
            if current_time - last_print_time >= print_interval:
                last_print_time = current_time
                clear_screen()
                i = 0
                s = ''
                for a in args:
                    if is_int(a):
                        s += f'{i:>3.0f}: {a:>20.0f}   '
                    else:    
                        s += f'{i:>3.0f}: {a:>20.10f}   '
                    if i % 3 == 0:
                        s += f'\n'
                    i += 1
                    if i > 100:
                        break
                print(f"{address}: {s}", end='\r', flush=True)

# Setup OSC handling
dispatcher = dispatcher.Dispatcher()
dispatcher.map("/*", print_handler)

# Setup OSC Server
server = osc_server.ThreadingOSCUDPServer(('0.0.0.0', 5000), dispatcher)
print("Listening for OSC on port 5000...")

# Run the server
server.serve_forever()
