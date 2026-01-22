"""
Ghost-QC Remote Client CLI

Command-line interface for running the Ghost-QC remote client.
"""

import argparse
import asyncio
import platform
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Ghost-QC Remote Client - Execute browser tests locally while connected to a remote server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect to local server
  python -m client.cli --server ws://localhost:8000/api/v1/remote/ws

  # Connect to remote server with custom name
  python -m client.cli --server ws://192.168.1.100:8000/api/v1/remote/ws --name "MyPC"

  # Disable auto-reconnect
  python -m client.cli --server ws://localhost:8000/api/v1/remote/ws --no-reconnect

For more information, visit: https://github.com/ghost-qc/ghost-qc
        """
    )

    parser.add_argument(
        "--server", "-s",
        required=True,
        help="WebSocket URL of the Ghost-QC server (e.g., ws://localhost:8000/api/v1/remote/ws)"
    )

    parser.add_argument(
        "--name", "-n",
        default=None,
        help=f"Name for this client (default: {platform.node()})"
    )

    parser.add_argument(
        "--no-reconnect",
        action="store_true",
        help="Disable auto-reconnect on disconnect"
    )

    parser.add_argument(
        "--reconnect-delay",
        type=int,
        default=5,
        help="Seconds to wait before reconnecting (default: 5)"
    )

    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=30,
        help="Seconds between heartbeats (default: 30)"
    )

    args = parser.parse_args()

    # Validate server URL
    if not args.server.startswith(("ws://", "wss://")):
        print("Error: Server URL must start with ws:// or wss://")
        sys.exit(1)

    # Print banner
    print_banner()

    # Print connection info
    print(f"Server: {args.server}")
    print(f"Client name: {args.name or platform.node()}")
    print(f"Auto-reconnect: {'Enabled' if not args.no_reconnect else 'Disabled'}")
    print()

    # Run client
    try:
        from .remote_client import run_client

        asyncio.run(
            run_client(
                server_url=args.server,
                client_name=args.name,
                auto_reconnect=not args.no_reconnect,
                reconnect_delay=args.reconnect_delay,
            )
        )
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Install required packages: pip install websockets playwright")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_banner():
    """Print welcome banner."""
    print("""
  ____  _               _          ___   ____
 / ___|| |__   ___  ___| |_       / _ \ / ___|
| |  _ | '_ \ / _ \/ __| __|____ | | | | |
| |_| || | | | (_) \__ \ ||_____|| |_| | |___
 \____||_| |_|\___/|___/\__|      \__\_\\____|

         Remote Client v1.0.0
    """)


if __name__ == "__main__":
    main()
