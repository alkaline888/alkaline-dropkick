#!/bin/bash

#installing from scratch
echo "[*] Installing python"
#trying with root and without root.
sudo pkg install python
pkg install python
sudo apt install python
apt install python
sudo apt-get install python
apt-get install python
sudo pacman -Syyu p

# Define the repository URL
REPO_URL="https://github.com/alkaline888/alkaline-dropkick"

# Define the directory to clone the repository into
REPO_DIR="alkaline"

# Clone the repository
echo "[*] Cloning repository..."
git clone $REPO_URL $REPO_DIR

# Check if the clone was successful
if [ $? -eq 0 ]; then
    echo "[*] Repository cloned successfully."

    # Change to the repository directory
    cd $REPO_DIR

    # Install the dependencies
    echo "[*] Installing dependencies..."
    pip install -r requirements.txt

    # Check if the installation was successful
    if [ $? -eq 0 ]; then
        echo "[*] Dependencies installed successfully."

        # Run the userbot
        echo "[*] Running userbot..."
        python donut.py

        # Exit message
        echo "Success!"
    else
        echo "[!] Failed to install dependencies."
        exit 1
    fi
else
    echo "[!] Failed to clone repository."
    exit 1
fi 
