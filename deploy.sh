#!/bin/bash

# --- Configuration ---
APP_DIR=/home/ubuntu/ci-cd-pipeline-demo
VENV_DIR=$APP_DIR/venv

# 1. Stop the running Flask app (if any)
pkill -f "python3 app.py" || true

# 2. Setup Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 3. Install/Update dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# 4. Start the application in the background
echo "Starting application..."
# Use VENV's python interpreter
nohup python3 "$APP_DIR/app.py" > /dev/null 2>&1 &

# 5. Deactivate
deactivate

echo "Deployment finished."