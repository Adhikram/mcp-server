#!/bin/bash

# Exit on any error
set -e

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "$DIR/.venv" ]; then
    /Users/mac/.local/bin/uv venv "$DIR/.venv"
fi

# Activate virtual environment
source "$DIR/.venv/bin/activate"

# Install dependencies if requirements.txt exists
if [ -f "$DIR/requirements.txt" ]; then
    /Users/mac/.local/bin/uv pip install -r "$DIR/requirements.txt"
fi

# Run the server with the provided connection string
python "$DIR/src/server.py"