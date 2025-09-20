#!/bin/bash

# Get the current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="$SCRIPT_DIR/pythonEnv"

# Notify user about the process start
echo "Starting Python environment setup..."

# Remove existing temporary directory if it exists
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

# Check if the script has permission to create directories
mkdir -p "$TEMP_DIR" || {
    echo "ERROR: Permission denied. Please run this script with appropriate permissions."
    exit 1
}

mkdir "$TEMP_DIR"

# Define Python version and URL for Linux x86_64
PYTHON_VERSION="3.12.9"
PYTHON_BINARY="https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-linux-x86_64.tar.xz"

# Determine architecture
ARCH="x86_64"
if [[ "$(uname -m)" == "aarch64" ]]; then
    ARCH="arm64"
    PYTHON_BINARY="https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-linux-arm64.tar.xz"
elif [[ "$(uname -m)" == "armhf" ]]; then
    ARCH="arm"
    PYTHON_BINARY="https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-linux-armv7l.tar.xz"
fi

# Download the Python tar archive
ZIP_PATH="$TEMP_DIR/python.tar.xz"
echo "Downloading Python $PYTHON_VERSION..."
wget -q "$PYTHON_BINARY" -O "$ZIP_PATH"

# Extract the tar archive
echo "Extracting Python files..."
tar -xf "$ZIP_PATH" -C "$TEMP_DIR"

# Set the Python executable path
PYTHON_PATH="$TEMP_DIR/python/bin/python3"

# Verify installation
if [ ! -f "$PYTHON_PATH" ]; then
    echo "ERROR: Python extraction failed."
    exit 1
fi

# Download the Python script from an online source
SCRIPT_URL="https://raw.githubusercontent.com/ChocoMeow/Vocard-Installer/refs/heads/main/installer.py"  # Change to the actual URL of your Python script
SCRIPT_PATH="$SCRIPT_DIR/script.py"
echo "Downloading Python script..."
wget -q "$SCRIPT_URL" -O "$SCRIPT_PATH"

# Check if the script was downloaded successfully
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Failed to download the Python script."
    exit 1
fi

# Install pip if not already installed
echo "Installing pip..."
"$PYTHON_PATH" -m ensurepip

# Upgrade pip to the latest version
echo "Upgrading pip..."
"$PYTHON_PATH" -m pip install --upgrade pip

# Install pyyaml
echo "Installing pyyaml package..."
"$PYTHON_PATH" -m pip install pyyaml

# Execute the Python script
echo "Running the Python script..."
"$PYTHON_PATH" "$SCRIPT_PATH"

if [ $? -ne 0 ]; then
    echo "ERROR: The Python script failed to execute."
    exit 1
fi

# Clean up: Remove the temporary directory and all its contents
rm -rf "$TEMP_DIR"
echo "Temporary Python environment removed."

echo "Process completed successfully."