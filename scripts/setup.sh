#!/bin/bash

# Setup script for Asterion

echo "Setting up Python Backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

echo "Setting up Node Frontend..."
cd frontend
npm install
cd ..

echo "Setup Complete!"
