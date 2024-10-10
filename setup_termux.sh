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

apt update
apt install python3

#TODO: install all the rest