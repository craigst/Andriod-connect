#!/bin/bash

# ADB Device Manager - Start Script

echo "🚀 Starting ADB Device Manager Web Server..."
echo ""

# Create necessary directories
mkdir -p logs data apk templates static

# Activate virtual environment and start server
echo "📦 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/bin/activate

echo "🌐 Starting Flask server on http://0.0.0.0:5020"
echo "   Access locally: http://localhost:5020"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python server.py
