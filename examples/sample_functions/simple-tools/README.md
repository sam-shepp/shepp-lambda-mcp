# Simple Tools Lambda Function

A beginner-friendly Lambda function demonstrating the MCP tool discovery protocol with simple, easy-to-understand tools.

## Overview

This Lambda function exposes **4 simple tools** that are perfect for learning how to implement the tool discovery protocol:

1. **hello_world** - Simple greeting tool
2. **echo** - Message echo with formatting options
3. **get_timestamp** - Current timestamp in various formats
4. **calculate** - Basic arithmetic operations

## Tools

### 1. hello_world

Returns a personalized greeting message.

**Input Schema:**
```json
{
  "name": "string (optional)"
}
```

**Example:**
```json
{
  "tool": "hello_world",
  "arguments": {
    "name": "Alice"
  }
}
```

**Response:**
```json
{
  "greeting": "Hello, Alice!",
  "message": "Welcome to the MCP Lambda Tool Server. This greeting was generated at 2026-04-30T09:00:00.000Z",
  "tool": "hello_world"
}
```

### 2. echo

Echoes back a message with optional formatting (uppercase, repeat).

**Input Schema:**
```json
{
  "message": "string (required)",
  "uppercase": "boolean (optional, default: false)",
  "repeat": "integer (optional, default: 1, min: 1, max: 10)"
}
```

**Example:**
```json
{
  "tool": "echo",
  "arguments": {
    "message": "Hello MCP",
    "uppercase": true,
    "repeat": 3
  }
}
```

**Response:**
```json
{
  "original": "Hello MCP",
  "echoed": "HELLO MCP HELLO MCP HELLO MCP",
  "uppercase": true,
  "repeat_count": 3,
  "length": 32,
  "tool": "echo"
}
```

### 3. get_timestamp

Returns the current server timestamp in various formats.

**Input Schema:**
```json
{
  "format": "string (optional, enum: ['iso', 'unix', 'readable'], default: 'iso')",
  "timezone": "string (optional, default: 'UTC')"
}
```

**Example:**
```json
{
  "tool": "get_timestamp",
  "arguments": {
    "format": "readable"
  }
}
```

**Response:**
```json
{
  "timestamp": "2026-04-30 09:00:00 UTC",
  "format": "Human readable",
  "timezone": "UTC",
  "tool": "get_timestamp"
}
```

### 4. calculate

Performs basic arithmetic calculations.

**Input Schema:**
```json
{
  "operation": "string (required, enum: ['add', 'subtract', 'multiply', 'divide'])",
  "a": "number (required)",
  "b": "number (required)"
}
```

**Example:**
```json
{
  "tool": "calculate",
  "arguments": {
    "operation": "multiply",
    "a": 7,
    "b": 6
  }
}
```

**Response:**
```json
{
  "operation": "multiply",
  "operand_a": 7,
  "operand_b": 6,
  "result": 42,
  "tool": "calculate"
}
```

## Implementation Details

### Tool Discovery Protocol

The function implements the tool discovery protocol by:

1. **Responding to discovery requests**: When called with `{"action": "discover_tools"}`, it returns all tool definitions
2. **Routing tool invocations**: Based on the `tool` field, it routes to the appropriate handler
3. **Supporting both formats**: Accepts both `{"tool": "...", "arguments": {...}}` and legacy flat format

### Code Structure

```python
def get_tool_definitions() -> Dict[str, Any]:
    """Returns tool definitions for MCP server discovery"""
    return {"tools": [...]}

def hello_world(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Tool implementation"""
    pass

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main handler with discovery and routing logic"""
    if event.get("action") == "discover_tools":
        return get_tool_definitions()
    
    # Route to tool handlers...
```

## Testing Locally

You can test the function locally using the AWS SAM CLI:

```bash
# Test discovery
sam local invoke SimpleToolsFunction -e events/discover.json

# Test hello_world
sam local invoke SimpleToolsFunction -e events/hello_world.json

# Test echo
sam local invoke SimpleToolsFunction -e events/echo.json

# Test get_timestamp
sam local invoke SimpleToolsFunction -e events/timestamp.json

# Test calculate
sam local invoke SimpleToolsFunction -e events/calculate.json
```

## Deployment

Deploy using AWS SAM:

```bash
cd examples/sample_functions
sam build
sam deploy --guided
```

## MCP Server Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "simple-tools": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FUNCTION_LIST": "SimpleToolsFunction"
      }
    }
  }
}
```

The MCP server will discover and register these tools:
- `hello_world`
- `echo`
- `get_timestamp`
- `calculate`

## Learning Path

This function is designed as a learning resource. Study the code to understand:

1. **Tool Discovery**: How to implement `get_tool_definitions()`
2. **Input Validation**: How to validate and handle parameters
3. **Error Handling**: How to return meaningful error messages
4. **Schema Design**: How to write clear JSON schemas
5. **Tool Routing**: How to route requests to handlers

## Next Steps

After understanding this example:

1. Try modifying the tools (add new parameters, change behavior)
2. Add your own simple tool
3. Study the CustomerManagement example for more complex patterns
4. Build your own Lambda function with custom tools

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License, Version 2.0.
