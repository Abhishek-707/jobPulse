#!/bin/bash
# Setup and run the sandbox

echo "Setting up sandbox..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Starting sandbox on http://localhost:5000"
python app.py
