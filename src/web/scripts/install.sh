#!/bin/bash

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version
get_python_version() {
    python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'
}

# Check for Python and pip
echo -e "Checking dependencies...\n"

# Check Python version
if ! command_exists python3; then
    echo -e "Python 3 not found. Installing...\n"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation using Homebrew
        if ! command_exists brew; then
            echo -e "Homebrew not found. Installing Homebrew...\n"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.12
    else
        # Linux installation
        sudo apt-get update
        sudo apt-get install -y python3.12
    fi
fi

# Verify Python version - TODO include AL2023
PYTHON_VERSION=$(get_python_version)
if (( $(echo "$PYTHON_VERSION < 3.12" | bc -l) )); then
    echo -e "Python version $PYTHON_VERSION is below 3.12\n"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.12
    else
        sudo apt-get update
        sudo apt-get install -y python3.12
    fi
else
    echo -e "Python version $PYTHON_VERSION is compatible\n"
fi

# Check for pip
if ! command_exists pip3; then
    echo -e "pip3 not found. Installing...\n"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install pip3
    else
        sudo apt-get install -y python3-pip
    fi
else
    echo -e "Found pip3. Updating...\n"
    pip3 install --upgrade pip
fi

# Verify installations
echo -e "Verifying installations...\n"
python3 --version
pip3 --version

echo -e "All dependencies installed successfully!\n"

echo -e "Installing requirements...\n"

pip install -r ../requirements.txt

echo -e "Done!\n"