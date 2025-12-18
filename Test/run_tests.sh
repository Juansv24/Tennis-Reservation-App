#!/bin/bash
# Quick start script for Linux/macOS

echo "========================================"
echo "Tennis Reservation App - Concurrent Tests"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    echo
    exit 1
fi

# Run setup (create test users if needed)
echo "Setting up test users..."
python setup_test_users.py
echo

# Run tests
echo "Starting concurrent tests..."
echo
python concurrent_test.py "$@"

echo
echo "========================================"
echo "Tests completed!"
echo "Check test_logs/ folder for detailed results"
echo "========================================"
