#!/bin/bash

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
        python alkaline.py

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
