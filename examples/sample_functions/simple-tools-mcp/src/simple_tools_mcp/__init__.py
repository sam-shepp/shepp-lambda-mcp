"""Simple Tools MCP Server - Dual-mode Lambda/MCP server."""

__version__ = "1.0.0"

from .lambda_handler import lambda_handler
from .server import main

__all__ = ["lambda_handler", "main", "__version__"]
