#!/bin/bash
# Setup script for JPEG AI Web Pipeline Python environment

echo "Setting up Python virtual environment for JPEG AI Web Pipeline..."

cd py

# Check if venv already exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Activating..."
else
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing Python dependencies with CUDA support..."
pip install --upgrade pip

# Install PyTorch with CUDA support first
echo "Installing PyTorch with CUDA support..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
echo "Installing other requirements..."
pip install -r requirements.txt

echo "Setup complete! To activate the environment, run:"
echo "cd py && source venv/bin/activate"