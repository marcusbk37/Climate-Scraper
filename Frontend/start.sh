#!/bin/bash

echo "🚀 Starting Article Search Frontend..."
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the Frontend directory."
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask, supabase, pinecone" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check if .env file exists in parent Embedding directory
if [ ! -f "../Embedding/.env" ]; then
    echo "⚠️  Warning: No .env file found in Embedding directory."
    echo "   Make sure your environment variables are set correctly."
fi

echo "✅ Starting the application..."
echo "🌐 Open your browser and go to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 app.py
