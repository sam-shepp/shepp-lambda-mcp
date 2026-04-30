# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simple Tools Lambda Function with Tool Discovery Protocol

This example demonstrates basic tool implementations using the tool discovery protocol.
Perfect for learning and testing the MCP server integration.
"""

import json
from typing import Any, Dict
from datetime import datetime


def get_tool_definitions() -> Dict[str, Any]:
    """
    Return tool definitions for the discovery protocol.
    
    This function is called when the MCP server sends {"action": "discover_tools"}
    during initialization to discover what tools this Lambda function provides.
    
    Returns:
        dict: Tool definitions with name, description, and inputSchema for each tool
    """
    return {
        "tools": [
            {
                "name": "hello_world",
                "description": "A simple greeting tool that returns a hello message. Optionally accepts a name to personalize the greeting.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Optional name to include in the greeting. If not provided, uses 'World'"
                        }
                    }
                }
            },
            {
                "name": "echo",
                "description": "Echoes back the provided message with optional formatting. Useful for testing and debugging.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to echo back"
                        },
                        "uppercase": {
                            "type": "boolean",
                            "description": "If true, converts the message to uppercase",
                            "default": False
                        },
                        "repeat": {
                            "type": "integer",
                            "description": "Number of times to repeat the message",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "get_timestamp",
                "description": "Returns the current server timestamp in various formats. Useful for time-based operations and logging.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Timestamp format: 'iso' (ISO 8601), 'unix' (Unix epoch), or 'readable' (human-readable)",
                            "enum": ["iso", "unix", "readable"],
                            "default": "iso"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone for readable format (e.g., 'UTC', 'America/New_York')",
                            "default": "UTC"
                        }
                    }
                }
            },
            {
                "name": "calculate",
                "description": "Performs basic arithmetic calculations. Supports addition, subtraction, multiplication, and division.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The arithmetic operation to perform",
                            "enum": ["add", "subtract", "multiply", "divide"]
                        },
                        "a": {
                            "type": "number",
                            "description": "First operand"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second operand"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            }
        ]
    }


def hello_world(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a greeting message.
    
    Args:
        arguments: Dict optionally containing name
        
    Returns:
        dict: Greeting message
    """
    name = arguments.get("name", "World")
    
    return {
        "greeting": f"Hello, {name}!",
        "message": f"Welcome to the MCP Lambda Tool Server. This greeting was generated at {datetime.utcnow().isoformat()}Z",
        "tool": "hello_world"
    }


def echo(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Echo back a message with optional formatting.
    
    Args:
        arguments: Dict containing message, uppercase (optional), and repeat (optional)
        
    Returns:
        dict: Echoed message with metadata
    """
    message = arguments.get("message")
    uppercase = arguments.get("uppercase", False)
    repeat = arguments.get("repeat", 1)
    
    if not message:
        return {"error": "Missing required field: message"}
    
    # Validate repeat count
    if not isinstance(repeat, int) or repeat < 1 or repeat > 10:
        return {"error": "repeat must be an integer between 1 and 10"}
    
    # Apply formatting
    formatted_message = message.upper() if uppercase else message
    
    # Repeat the message
    repeated_message = " ".join([formatted_message] * repeat)
    
    return {
        "original": message,
        "echoed": repeated_message,
        "uppercase": uppercase,
        "repeat_count": repeat,
        "length": len(repeated_message),
        "tool": "echo"
    }


def get_timestamp(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current timestamp in various formats.
    
    Args:
        arguments: Dict containing format (optional) and timezone (optional)
        
    Returns:
        dict: Timestamp in requested format
    """
    format_type = arguments.get("format", "iso")
    timezone = arguments.get("timezone", "UTC")
    
    now = datetime.utcnow()
    
    result = {
        "tool": "get_timestamp",
        "timezone": timezone
    }
    
    if format_type == "iso":
        result["timestamp"] = now.isoformat() + "Z"
        result["format"] = "ISO 8601"
    elif format_type == "unix":
        result["timestamp"] = int(now.timestamp())
        result["format"] = "Unix epoch (seconds)"
    elif format_type == "readable":
        result["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        result["format"] = "Human readable"
    else:
        return {"error": f"Invalid format: {format_type}. Must be 'iso', 'unix', or 'readable'"}
    
    return result


def calculate(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform basic arithmetic calculations.
    
    Args:
        arguments: Dict containing operation, a, and b
        
    Returns:
        dict: Calculation result or error
    """
    operation = arguments.get("operation")
    a = arguments.get("a")
    b = arguments.get("b")
    
    # Validate inputs
    if not all([operation, a is not None, b is not None]):
        return {"error": "Missing required fields: operation, a, and b are required"}
    
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return {"error": "Operands a and b must be numbers"}
    
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
                return {"error": "Division by zero is not allowed"}
            result = a / b
        else:
            return {
                "error": f"Invalid operation: {operation}",
                "valid_operations": ["add", "subtract", "multiply", "divide"]
            }
        
        return {
            "operation": operation,
            "operand_a": a,
            "operand_b": b,
            "result": result,
            "tool": "calculate"
        }
    except Exception as e:
        return {
            "error": "Calculation error",
            "message": str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler with tool discovery protocol support.
    
    This handler demonstrates the tool discovery protocol with simple, easy-to-understand tools:
    1. Responds to {"action": "discover_tools"} with tool definitions
    2. Routes tool invocations based on the "tool" field
    3. Supports both new format {"tool": "...", "arguments": {...}}
       and legacy format with flat parameters
    
    Args:
        event: Lambda event containing action, tool, or parameters
        context: AWS Lambda context object
        
    Returns:
        dict: Tool definitions, tool results, or error message
    """
    try:
        # Handle tool discovery request
        if event.get("action") == "discover_tools":
            return get_tool_definitions()
        
        # Determine tool name and arguments
        if "arguments" in event:
            # New format: {"tool": "...", "arguments": {...}}
            tool_name = event.get("tool")
            arguments = event["arguments"]
        else:
            # Legacy format: {"tool": "...", "message": "...", ...}
            tool_name = event.get("tool")
            arguments = {k: v for k, v in event.items() if k != "tool"}
        
        # Route to appropriate tool handler
        if tool_name == "hello_world":
            return hello_world(arguments)
        elif tool_name == "echo":
            return echo(arguments)
        elif tool_name == "get_timestamp":
            return get_timestamp(arguments)
        elif tool_name == "calculate":
            return calculate(arguments)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": [
                    "hello_world",
                    "echo",
                    "get_timestamp",
                    "calculate"
                ]
            }
            
    except Exception as e:
        return {
            "error": "Internal error",
            "message": str(e)
        }
