"""
Port Finder Utility
===================

Automatically find available ports for servers.
Prevents "port already in use" errors.

Author: PromptOps Team
Date: 2026-05-11
"""

import socket
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class PortFinder:
    """
    Utility to find available network ports.

    Features:
    - Check if port is available
    - Find next available port
    - Find multiple available ports
    - Port range scanning
    """

    @staticmethod
    def is_port_available(port: int, host: str = '0.0.0.0') -> bool:
        """
        Check if a port is available.

        Args:
            port: Port number to check
            host: Host address (default: 0.0.0.0)

        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return True
        except OSError:
            return False

    @staticmethod
    def find_available_port(
        start_port: int = 8000,
        max_tries: int = 100,
        host: str = '0.0.0.0'
    ) -> Optional[int]:
        """
        Find the next available port starting from start_port.

        Args:
            start_port: Starting port number
            max_tries: Maximum number of ports to try
            host: Host address

        Returns:
            Available port number, or None if no port found
        """
        for port in range(start_port, start_port + max_tries):
            if PortFinder.is_port_available(port, host):
                logger.info(f"Found available port: {port}")
                return port

        logger.error(f"No available port found in range {start_port}-{start_port + max_tries}")
        return None

    @staticmethod
    def find_multiple_ports(
        count: int,
        start_port: int = 8000,
        max_tries: int = 100,
        host: str = '0.0.0.0'
    ) -> List[int]:
        """
        Find multiple available ports.

        Args:
            count: Number of ports needed
            start_port: Starting port number
            max_tries: Maximum number of ports to try
            host: Host address

        Returns:
            List of available port numbers
        """
        ports = []
        current_port = start_port

        for _ in range(count):
            port = PortFinder.find_available_port(current_port, max_tries, host)
            if port is None:
                logger.warning(f"Could only find {len(ports)} out of {count} ports")
                break
            ports.append(port)
            current_port = port + 1

        return ports

    @staticmethod
    def get_port_with_fallback(
        preferred_port: int,
        fallback_start: int = 8000,
        host: str = '0.0.0.0'
    ) -> int:
        """
        Try to use preferred port, fallback to finding available port.

        Args:
            preferred_port: Preferred port number
            fallback_start: Starting port for fallback search
            host: Host address

        Returns:
            Port number to use

        Raises:
            RuntimeError: If no port available
        """
        # Try preferred port first
        if PortFinder.is_port_available(preferred_port, host):
            logger.info(f"Using preferred port: {preferred_port}")
            return preferred_port

        logger.warning(f"Port {preferred_port} is busy, finding alternative...")

        # Find alternative
        alt_port = PortFinder.find_available_port(fallback_start, max_tries=100, host=host)
        if alt_port is None:
            raise RuntimeError(f"No available ports found (tried {fallback_start}-{fallback_start+100})")

        logger.info(f"Using alternative port: {alt_port}")
        return alt_port

    @staticmethod
    def scan_port_range(
        start_port: int,
        end_port: int,
        host: str = '0.0.0.0'
    ) -> List[int]:
        """
        Scan a range of ports and return available ones.

        Args:
            start_port: Start of range
            end_port: End of range (inclusive)
            host: Host address

        Returns:
            List of available ports in range
        """
        available = []
        for port in range(start_port, end_port + 1):
            if PortFinder.is_port_available(port, host):
                available.append(port)

        logger.info(f"Found {len(available)} available ports in range {start_port}-{end_port}")
        return available


def find_port(preferred: int = 8000, host: str = '0.0.0.0') -> int:
    """
    Convenience function to find available port.

    Args:
        preferred: Preferred port number
        host: Host address

    Returns:
        Available port number

    Raises:
        RuntimeError: If no port available
    """
    return PortFinder.get_port_with_fallback(preferred, preferred, host)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Port Finder Test")
    print("=" * 50)

    # Test 1: Check specific port
    port = 8000
    available = PortFinder.is_port_available(port)
    print(f"\nPort {port} available: {available}")

    # Test 2: Find available port
    port = PortFinder.find_available_port(8000)
    print(f"\nNext available port from 8000: {port}")

    # Test 3: Find multiple ports
    ports = PortFinder.find_multiple_ports(5, 8000)
    print(f"\n5 available ports: {ports}")

    # Test 4: Preferred port with fallback
    try:
        port = PortFinder.get_port_with_fallback(preferred_port=8000, fallback_start=8000)
        print(f"\nUsing port: {port}")
    except RuntimeError as e:
        print(f"\nError: {e}")

    # Test 5: Scan range
    available_ports = PortFinder.scan_port_range(8000, 8010)
    print(f"\nAvailable ports in range 8000-8010: {available_ports}")

    print("\n" + "=" * 50)
    print("All tests completed!")
