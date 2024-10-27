#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python not found. Installing Python..."
    sudo apt update
    sudo apt install -y python3 python3-pip
else
    echo "Python is already installed."
fi

# Install packages from requirements.txt
echo "Installing requirements..."
pip3 install -r requirements.txt
