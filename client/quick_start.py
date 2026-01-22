#!/usr/bin/env python3
"""
Ghost-QC Quick Start Client

A simple script to connect to a Ghost-QC server with minimal setup.
Auto-installs dependencies if needed.
"""

import subprocess
import sys
import platform


def check_and_install(package, import_name=None):
    """Check if package is installed, install if not."""
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True


def main():
    print("""
  ____  _               _          ___   ____
 / ___|| |__   ___  ___| |_       / _ \\ / ___|
| |  _ | '_ \\ / _ \\/ __| __|_____| | | | |
| |_| || | | | (_) \\__ \\ ||_____|| |_| | |___
 \\____||_| |_|\\___/|___/\\__|      \\__\\_\\____|

         Quick Start Client
    """)

    # Check and install dependencies
    print("Checking dependencies...")
    check_and_install("websockets")
    check_and_install("playwright")

    # Check if playwright browsers are installed
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get chromium path
            p.chromium.executable_path
    except Exception:
        print("Installing Playwright browser...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

    # Get server URL
    print()
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = input("Enter server URL (e.g., ws://192.168.1.100:8000/api/v1/remote/ws): ").strip()

    if not server_url:
        print("Error: Server URL is required")
        sys.exit(1)

    if not server_url.startswith(("ws://", "wss://")):
        print("Error: Server URL must start with ws:// or wss://")
        sys.exit(1)

    # Get client name
    if len(sys.argv) > 2:
        client_name = sys.argv[2]
    else:
        client_name = platform.node()

    print(f"\nConnecting to: {server_url}")
    print(f"Client name: {client_name}")
    print()

    # Import and run the client
    import asyncio
    from client.remote_client import run_client

    try:
        asyncio.run(run_client(server_url, client_name))
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
