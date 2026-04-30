"""Simple Tools - Tool implementations.

All tools are registered with ChukMCPServer via @tool decorators.
"""

import json
from datetime import datetime
from typing import Callable, Dict

from chuk_mcp_server import tool

# Tool registry for Lambda handler
TOOLS: Dict[str, Callable] = {}


@tool(name='hello_world')
def hello_world(name: str = "World") -> str:
    """
    A simple greeting tool that returns a hello message.
    
    Args:
        name: Optional name to include in the greeting. If not provided, uses 'World'
    
    Returns:
        Greeting message with timestamp
    """
    greeting = f"Hello, {name}!"
    message = f"Welcome to the MCP Lambda Tool Server. This greeting was generated at {datetime.utcnow().isoformat()}Z"
    
    return json.dumps({
        "greeting": greeting,
        "message": message,
        "tool": "hello_world"
    }, indent=2)


@tool(name='echo')
def echo(message: str, uppercase: bool = False, repeat: int = 1) -> str:
    """
    Echoes back the provided message with optional formatting.
    
    Args:
        message: The message to echo back
        uppercase: If true, converts the message to uppercase
        repeat: Number of times to repeat the message (1-10)
    
    Returns:
        Echoed message with metadata
    """
    # Validate repeat count
    if not isinstance(repeat, int) or repeat < 1 or repeat > 10:
        return json.dumps({"error": "repeat must be an integer between 1 and 10"})
    
    # Apply formatting
    formatted_message = message.upper() if uppercase else message
    
    # Repeat the message
    repeated_message = " ".join([formatted_message] * repeat)
    
    return json.dumps({
        "original": message,
        "echoed": repeated_message,
        "uppercase": uppercase,
        "repeat_count": repeat,
        "length": len(repeated_message),
        "tool": "echo"
    }, indent=2)


@tool(name='get_timestamp')
def get_timestamp(format: str = "iso", timezone: str = "UTC") -> str:
    """
    Returns the current server timestamp in various formats.
    
    Args:
        format: Timestamp format - 'iso' (ISO 8601), 'unix' (Unix epoch), or 'readable' (human-readable)
        timezone: Timezone for readable format (e.g., 'UTC', 'America/New_York')
    
    Returns:
        Timestamp in requested format
    """
    now = datetime.utcnow()
    
    result = {
        "tool": "get_timestamp",
        "timezone": timezone
    }
    
    if format == "iso":
        result["timestamp"] = now.isoformat() + "Z"
        result["format"] = "ISO 8601"
    elif format == "unix":
        result["timestamp"] = int(now.timestamp())
        result["format"] = "Unix epoch (seconds)"
    elif format == "readable":
        result["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        result["format"] = "Human readable"
    else:
        return json.dumps({"error": f"Invalid format: {format}. Must be 'iso', 'unix', or 'readable'"})
    
    return json.dumps(result, indent=2)


@tool(name='calculate')
def calculate(operation: str, a: float, b: float) -> str:
    """
    Performs basic arithmetic calculations.
    
    Args:
        operation: The arithmetic operation - 'add', 'subtract', 'multiply', or 'divide'
        a: First operand
        b: Second operand
    
    Returns:
        Calculation result or error
    """
    # Validate inputs
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return json.dumps({"error": "Operands a and b must be numbers"})
    
    # Perform calculation
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return json.dumps({"error": "Division by zero is not allowed"})
            result = a / b
        else:
            return json.dumps({
                "error": f"Invalid operation: {operation}",
                "valid_operations": ["add", "subtract", "multiply", "divide"]
            })
        
        return json.dumps({
            "operation": operation,
            "operand_a": a,
            "operand_b": b,
            "result": result,
            "tool": "calculate"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Calculation error",
            "message": str(e)
        })


# Register tools in the TOOLS dict for Lambda handler
TOOLS['hello_world'] = hello_world
TOOLS['echo'] = echo
TOOLS['get_timestamp'] = get_timestamp
TOOLS['calculate'] = calculate

__all__ = ["hello_world", "echo", "get_timestamp", "calculate", "TOOLS"]