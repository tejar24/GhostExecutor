#!/bin/bash

echo ""
echo "  ____  _               _          ___   ____ "
echo " / ___|| |__   ___  ___| |_       / _ \ / ___|"
echo "| |  _ | '_ \ / _ \/ __| __|_____| | | | |    "
echo "| |_| || | | | (_) \__ \ ||_____|| |_| | |___ "
echo " \____||_| |_|\___/|___/\__|      \__\_\____|"
echo ""
echo "         Remote Client Launcher"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

# Check if websockets is installed
if ! python3 -c "import websockets" &> /dev/null; then
    echo "Installing websockets..."
    pip3 install websockets
fi

# Check if playwright is installed
if ! python3 -c "import playwright" &> /dev/null; then
    echo "Installing playwright..."
    pip3 install playwright
    echo "Installing browser binaries..."
    playwright install chromium
fi

# Get server URL
if [ -z "$1" ]; then
    read -p "Enter server URL (e.g., ws://192.168.1.100:8000/api/v1/remote/ws): " SERVER_URL
else
    SERVER_URL=$1
fi

# Get client name (optional)
if [ -z "$2" ]; then
    CLIENT_NAME=$(hostname)
else
    CLIENT_NAME=$2
fi

echo ""
echo "Starting client..."
echo "Server: $SERVER_URL"
echo "Client Name: $CLIENT_NAME"
echo ""

# Get script directory and go to parent
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

python3 -m client.cli --server "$SERVER_URL" --name "$CLIENT_NAME"
