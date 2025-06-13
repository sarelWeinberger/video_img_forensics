#!/bin/bash

# Start the Manipulated Score Python Service
# This script is used to start the Python service when the Java service starts

# Set the port for the Python service
PORT=5000

# Set to true if you want to use a virtual environment
USE_VENV=false

# Check if a port was provided as an argument
if [ $# -eq 1 ]; then
    PORT=$1
fi

# Check if a second argument is provided for virtual environment
if [ $# -eq 2 ]; then
    if [ "$2" = "venv" ]; then
        USE_VENV=true
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run this service."
    exit 1
fi

# Install the correct version of Werkzeug first to avoid dependency conflicts
echo "Installing Werkzeug 2.0.1 to avoid dependency conflicts..."
pip install werkzeug==2.0.1

# Install other dependencies
echo "Installing other dependencies..."
pip install -r requirements.txt

# Check if virtual environment is needed
if [ "$USE_VENV" = "true" ]; then
    # Check if python3-venv is installed
    if ! dpkg -l | grep -q python3-venv; then
        echo "python3-venv is not installed. You may need to install it with:"
        echo "sudo apt install python3.8-venv"
        echo "Continuing without virtual environment..."
    else
        # Check if the virtual environment exists
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi

        # Activate the virtual environment
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        # Install dependencies in the virtual environment
        echo "Installing dependencies in virtual environment..."
        pip install werkzeug==2.0.1
        pip install -r requirements.txt
    fi
fi

# Check if port is already in use
if netstat -tuln | grep -q ":$PORT "; then
    echo "Port $PORT is already in use. Please stop the process using this port or use a different port."
    exit 1
fi

# Start the Python service
echo "Starting Manipulated Score Python Service on port $PORT..."
python3 manipulated_score_service.py $PORT