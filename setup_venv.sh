#!/bin/bash

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found in the current directory."
    exit 1
fi

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Virtual environment 'venv' already exists. Deleting old 'venv'..."
    rm -rf venv
fi

# Create a new virtual environment named venv
echo "Creating virtual environment 'venv'..."
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Ensure pip is installed in the virtual environment
echo "Installing/upgrading pip..."
python3 -m ensurepip --upgrade

## installing pytorch stuff
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install requirements
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

# Deactivate the virtual environment
deactivate

echo "Setup complete."

echo "To activate the venv, run \"source venv/bin/activate\" "
