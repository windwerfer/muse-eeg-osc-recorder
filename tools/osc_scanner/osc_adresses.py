from pythonosc import dispatcher
from pythonosc import osc_server


import os
import time

def clear_screen():
    # Clear command for Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # Clear command for Unix/Linux/MacOS
    else:
        _ = os.system('clear')


list_only_new = True
list_only_new = False
list_stats = True

adr = []

def print_handler(address, *args):
    if list_only_new:
        if address not in adr:
            adr.append(address)
            print(f"{address}: {args}")
    elif list_stats:
        if address == '/muse_metrics':
            clear_screen()
            i = 0
            s = ''
            for a in args:
                s += f'{a}\n'
                i += 1
                if i > 20:
                    break
            print(f"{address}: {s}\r")
            #print(f"\r{address}: {args}", end='', flush=True)
    else:
        print(f"{address}: {args}")

# Set up a dispatcher that will handle incoming OSC messages
dispatcher = dispatcher.Dispatcher()
dispatcher.map("/*", print_handler)  # Map all addresses to our handler

# Set up the server to listen on port 5000
server = osc_server.ThreadingOSCUDPServer(('0.0.0.0', 5000), dispatcher)
print("Listening for OSC on port 5000...")

# This will keep the script running to listen for incoming OSC messages
server.serve_forever()
