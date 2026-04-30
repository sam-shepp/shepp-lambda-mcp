"""Simple Tools MCP Server — entry point.

Imports tool modules to register @tool decorators, then runs the server.
Can also be deployed as AWS Lambda function.
"""

import logging
import sys

from chuk_mcp_server import run

# Import tools to register them
from . import tools  # noqa: F401

# Re-export tool functions
from .tools import calculate, echo, get_timestamp, hello_world

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)

__all__ = [
    "calculate",
    "echo",
    "get_timestamp",
    "hello_world",
    "main",
]


def main():
    """Run the Simple Tools MCP server."""
    # Check if transport is specified in command line args
    # Default to stdio for MCP compatibility
    transport = "stdio"

    # Allow HTTP mode via command line
    if len(sys.argv) > 1 and sys.argv[1] in ["http", "--http"]:
        transport = "http"
        logger.warning("Starting Simple Tools MCP Server in HTTP mode")

    # Suppress chuk_mcp_server logging in STDIO mode
    if transport == "stdio":
        logging.getLogger("chuk_mcp_server").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.core").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.stdio_transport").setLevel(logging.ERROR)

    run(transport=transport)


if __name__ == "__main__":
    main()
