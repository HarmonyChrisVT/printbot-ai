#!/bin/bash

# PrintBot AI - Auto Installer for Mac/Linux
# ===========================================

set -e

echo "=========================================="
echo "   PrintBot AI - Automatic Installer"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Python is installed
print_status "Checking for Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_success "Python is already installed"
    $PYTHON_CMD --version
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    print_success "Python is already installed"
    $PYTHON_CMD --version
else
    print_warning "Python not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_status "Detected macOS"
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        print_status "Installing Python via Homebrew..."
        brew install python
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_status "Detected Linux"
        
        # Detect package manager
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            print_status "Installing Python via apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            print_status "Installing Python via yum..."
            sudo yum install -y python3 python3-pip
        elif command -v dnf &> /dev/null; then
            # Fedora
            print_status "Installing Python via dnf..."
            sudo dnf install -y python3 python3-pip
        else
            print_error "Could not detect package manager. Please install Python manually."
            exit 1
        fi
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    PYTHON_CMD="python3"
    print_success "Python installed successfully!"
fi

echo ""
echo "=========================================="
echo "   Installing Dependencies"
echo "=========================================="
echo ""

# Upgrade pip
print_status "Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install requirements
print_status "Installing required packages..."
if [ -f "python/requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r python/requirements.txt
    print_success "Dependencies installed!"
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "   Creating Environment File"
echo "=========================================="
echo ""

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_success ".env file created!"
        echo ""
        print_warning "IMPORTANT: Edit .env file with your API keys!"
        echo "   - Shopify Store URL"
        echo "   - Shopify Admin API Token"
        echo "   - Printful API Key"
        echo "   - OpenAI API Key"
    else
        print_warning ".env.example not found. You'll need to create .env manually."
    fi
else
    print_success ".env file already exists"
fi

echo ""
echo "=========================================="
echo "   Setup Complete!"
echo "=========================================="
echo ""
print_success "PrintBot AI is ready!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys"
echo "   nano .env  (or use any text editor)"
echo ""
echo "2. Run the system:"
echo "   $PYTHON_CMD start.py"
echo ""
echo "3. Open in browser:"
echo "   http://localhost:8080"
echo ""
echo "Need help getting API keys?"
echo "Visit: https://nkzoe4rayvwts.ok.kimi.link/setup.html"
echo ""
