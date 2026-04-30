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
Simple Tools - Dual-Mode Lambda/MCP Server

This example demonstrates a Lambda function that can operate in two modes:
1. As a Lambda function (invoked via AWS Lambda invoke)
2. As a standalone MCP server (run directly with stdio transport)

Uses ChukMCPServer for MCP functionality.
"""

import json
import sys
from typing import Any, Dict
from datetime import datetime
from chuk_mcp_server import ChukMCPServer


# Initialize MCP Server
mcp = ChukMCPServer(
    name='simple-tools',
    version='1.0.0',
    description='Simple example tools: hello_world, echo, get_timestamp, calculate',
    transport='stdio',
)


@mcp.tool(name='hello_world')
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


@mcp.tool(name='echo')
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


@mcp.tool(name='get_timestamp')
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


@mcp.tool(name='calculate')
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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler that supports tool discovery protocol.
    
    This handler allows the Lambda function to work with shepp-lambda-mcp
    by responding to discovery requests and routing tool invocations.
    
    Args:
        event: Lambda event containing action, tool, or parameters
        context: AWS Lambda context object
        
    Returns:
        dict: Tool definitions, tool results, or error message
    """
    try:
        # Handle tool discovery request
        if event.get("action") == "discover_tools":
            # Get tool definitions from ChukMCPServer
            tools = []
            for tool_name, tool_func in mcp._tools.items():
                # Extract schema from function signature and docstring
                import inspect
                sig = inspect.signature(tool_func)
                doc = inspect.getdoc(tool_func) or f"Tool: {tool_name}"
                
                # Build input schema from function signature
                properties = {}
                required = []
                
                for param_name, param in sig.parameters.items():
                    if param_name in ['self', 'ctx']:
                        continue
                    
                    param_type = "string"  # Default type
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                    
                    properties[param_name] = {
                        "type": param_type,
                        "description": f"Parameter: {param_name}"
                    }
                    
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
                
                tools.append({
                    "name": tool_name,
                    "description": doc.split('\n')[0],  # First line of docstring
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                })
            
            return {"tools": tools}
        
        # Handle tool invocation
        tool_name = event.get("tool")
        if not tool_name:
            return {"error": "Missing 'tool' field in request"}
        
        # Get arguments (support both formats)
        if "arguments" in event:
            arguments = event["arguments"]
        else:
            arguments = {k: v for k, v in event.items() if k != "tool"}
        
        # Get the tool function
        if tool_name not in mcp._tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(mcp._tools.keys())
            }
        
        tool_func = mcp._tools[tool_name]
        
        # Invoke the tool
        result = tool_func(**arguments)
        
        # Parse result if it's JSON string
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError:
            return {"result": result}
            
    except Exception as e:
        return {
            "error": "Internal error",
            "message": str(e),
            "type": type(e).__name__
        }


def main():
    """
    Main entry point for running as a standalone MCP server.
    
    This allows the Lambda function to be run directly as an MCP server
    using stdio transport, making it usable with any MCP client.
    """
    print("Starting Simple Tools MCP Server...", file=sys.stderr)
    print("Available tools: hello_world, echo, get_timestamp, calculate", file=sys.stderr)
    mcp.run()


if __name__ == '__main__':
    main()
