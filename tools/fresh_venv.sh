#!/bin/bash
# Fresh virtual environment setup for testing

echo "🧹 Creating fresh virtual environment..."

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo "Removing old .venv..."
    rm -rf .venv
fi

# Create new venv
echo "Creating new .venv..."
python -m venv .venv

# Activate venv
echo "Activating .venv..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-test.txt

# Check encoding
echo "Checking Python encoding..."
python -c "import sys; print(f'Default encoding: {sys.getdefaultencoding()}')"

echo "✅ Fresh virtual environment ready!"
echo "To activate: source .venv/bin/activate"
