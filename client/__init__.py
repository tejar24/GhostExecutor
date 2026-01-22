"""
Ghost-QC Remote Client

Client module for connecting to Ghost-QC server and executing browser commands locally.
"""

from .remote_client import RemoteClient, run_client

__all__ = [
    "RemoteClient",
    "run_client",
]
