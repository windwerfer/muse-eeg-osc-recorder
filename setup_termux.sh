#!/bin/bash

# Path where Termux typically creates a symlink for shared storage
STORAGE_SYMLINK=~/storage

# Check if the storage directory exists
if [ -e "$STORAGE_SYMLINK" ]; then
    echo "Termux storage setup has been completed already."
else
    echo "Termux storage does not appear to be set up. Please run 'termux-setup-storage'."
    termux-setup-storage
fi

pkg update
yes | pkg upgrade  # automatically send yes to install pa

# better to run it twice..
pkg update
yes | pkg upgrade  # automatically send yes to install pa

yes | pkg install python3
yes | pkg install build-essential python-numpy man matplotlib python-pillow python-tkinter python-pandas

# additional repo needs to be added for scipy
yes | pkg install tur-repo
pkg update

# advanced math functions for generating graphs
yes | pkg install python-scipy

# library for the osc server and the monitoring of the cpu
pip install wheel
pip install python-osc psutil

# audio support for nod reminder
yes | pkg install pulseaudio mpv

mkdir /sdcard/muse_rec_osc
mkdir /sdcard/muse_rec_osc/out_eeg
echo 'alias .r="cd /sdcard/muse_rec_osc" ' >> ~/.bashrc
echo 'alias r="cd /sdcard/muse_rec_osc ; python3 write_osc_to_files.py" ' >> ~/.bashrc
source .bashrc