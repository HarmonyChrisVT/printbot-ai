#!/bin/bash

echo "=========================================="
echo "   PRINTBOT AI - AUTOMATED STORE SYSTEM"
echo "=========================================="
echo ""
echo "This will set up everything automatically!"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python not found! Installing..."
    
    # Detect OS and install Python
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python
    else
        # Linux
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    fi
else
    echo "Python found! Version:"
    python3 --version
fi

echo ""
echo "Installing required packages..."
cd app
pip3 install -r requirements.txt

echo ""
echo "Setting up database..."
python3 -c "from database.models import init_db; init_db()"

echo ""
echo "=========================================="
echo "   SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Starting the dashboard..."
echo ""
echo "The dashboard will open in your browser at:"
echo "http://localhost:3000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Open browser (works on macOS and most Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
else
    xdg-open http://localhost:3000 2>/dev/null || sensible-browser http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
fi

python3 main.py
