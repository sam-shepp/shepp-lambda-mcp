# Simple Tools MCP - Dual-Mode Lambda/MCP Server

A Lambda function that can operate in **two modes**:
1. **Lambda Mode**: Deployed to AWS Lambda, invoked via shepp-lambda-mcp
2. **Standalone Mode**: Run directly as an MCP server with any MCP client

## Key Features

✅ **Dual-Mode Operation** - Works as Lambda function OR standalone MCP server
✅ **ChukMCPServer** - Uses chuk-mcp-server package for MCP functionality
✅ **Tool Discovery** - Supports shepp-lambda-mcp tool discovery protocol
✅ **Portable** - Same code runs anywhere (Lambda, local, container, etc.)
✅ **Type-Safe** - Python type hints throughout

## Architecture

This example demonstrates the **recommended pattern** for creating Lambda functions that are also MCP servers:

```python
from chuk_mcp_server import ChukMCPServer

# Initialize MCP Server
mcp = ChukMCPServer(name='simple-tools', version='1.0.0')

# Define tools using decorators
@mcp.tool(name='hello_world')
def hello_world(name: str = "World") -> str:
    """Tool implementation"""
    return json.dumps({"greeting": f"Hello, {name}!"})

# Lambda handler for AWS Lambda
def lambda_handler(event, context):
    """Handles tool discovery and invocation"""
    if event.get("action") == "discover_tools":
        return {"tools": [...]}  # Return tool definitions
    # Route to tool functions...

# Standalone entry point
if __name__ == '__main__':
    mcp.run()  # Run as MCP server
```

## Available Tools

### 1. hello_world
Simple greeting with optional name parameter.

### 2. echo
Echo messages with uppercase and repeat formatting options.

### 3. get_timestamp
Get current timestamp in ISO, Unix, or readable formats.

### 4. calculate
Basic arithmetic operations (add, subtract, multiply, divide).

## Usage

### Mode 1: As AWS Lambda Function

**Deploy to Lambda:**
```bash
cd examples/sample_functions
sam build
sam deploy
```

**Use with shepp-lambda-mcp:**
```json
{
  "mcpServers": {
    "simple-tools": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FUNCTION_LIST": "SimpleToolsMCPFunction"
      }
    }
  }
}
```

The shepp-lambda-mcp server will:
1. Call Lambda with `{"action": "discover_tools"}`
2. Register all 4 tools: `hello_world`, `echo`, `get_timestamp`, `calculate`
3. Route tool calls to the Lambda function

### Mode 2: As Standalone MCP Server

**Install dependencies:**
```bash
pip install chuk-mcp-server
```

**Run directly:**
```bash
python app.py
```

**Use with any MCP client:**
```json
{
  "mcpServers": {
    "simple-tools-local": {
      "command": "python",
      "args": ["/path/to/app.py"]
    }
  }
}
```

The same code runs as a native MCP server using stdio transport.

## Benefits of Dual-Mode Pattern

### 1. **Flexibility**
- Deploy to Lambda for production (scalable, serverless)
- Run locally for development (fast iteration)
- Run in containers, VMs, or anywhere Python runs

### 2. **Consistency**
- Same code, same behavior everywhere
- No separate implementations for Lambda vs MCP
- Single source of truth

### 3. **Developer Experience**
- Test locally without AWS
- Debug with standard Python tools
- Fast development cycle

### 4. **Cost Optimization**
- Use Lambda for production (pay per use)
- Use local/container for development (free)
- Choose deployment based on needs

## Implementation Details

### Tool Discovery Protocol

The Lambda handler implements the discovery protocol:

```python
def lambda_handler(event, context):
    # Discovery request
    if event.get("action") == "discover_tools":
        tools = []
        for tool_name, tool_func in mcp._tools.items():
            # Extract schema from function signature
            tools.append({
                "name": tool_name,
                "description": "...",
                "inputSchema": {...}
            })
        return {"tools": tools}
    
    # Tool invocation
    tool_name = event.get("tool")
    arguments = event.get("arguments", {})
    result = mcp._tools[tool_name](**arguments)
    return result
```

### ChukMCPServer Integration

ChukMCPServer provides:
- Tool registration via decorators
- Automatic schema generation
- stdio transport for standalone mode
- Tool routing and execution

### Type Safety

All tools use Python type hints:
```python
@mcp.tool(name='calculate')
def calculate(operation: str, a: float, b: float) -> str:
    """Type hints enable automatic schema generation"""
    pass
```

## Testing

### Test as Lambda Function

```bash
# Test discovery
aws lambda invoke \
  --function-name SimpleToolsMCPFunction \
  --payload '{"action": "discover_tools"}' \
  response.json

# Test tool invocation
aws lambda invoke \
  --function-name SimpleToolsMCPFunction \
  --payload '{"tool": "hello_world", "arguments": {"name": "Alice"}}' \
  response.json
```

### Test as Standalone Server

```bash
# Run the server
python app.py

# In another terminal, use an MCP client to test
# Or use the MCP inspector tool
```

## Deployment

### Lambda Deployment

The SAM template includes this function:

```yaml
SimpleToolsMCPFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: simple-tools-mcp/
    Handler: app.lambda_handler
    Runtime: python3.13
    Architectures:
      - arm64
```

### Standalone Deployment

**Docker:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
```

**Systemd Service:**
```ini
[Unit]
Description=Simple Tools MCP Server

[Service]
ExecStart=/usr/bin/python3 /path/to/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Migration Guide

To convert an existing Lambda function to dual-mode:

1. **Add ChukMCPServer:**
   ```python
   from chuk_mcp_server import ChukMCPServer
   mcp = ChukMCPServer(name='my-function', version='1.0.0')
   ```

2. **Convert functions to tools:**
   ```python
   @mcp.tool(name='my_tool')
   def my_tool(param: str) -> str:
       # Your existing logic
       pass
   ```

3. **Update lambda_handler:**
   ```python
   def lambda_handler(event, context):
       if event.get("action") == "discover_tools":
           return {"tools": [...]}
       # Route to tools
   ```

4. **Add main entry point:**
   ```python
   if __name__ == '__main__':
       mcp.run()
   ```

## Best Practices

1. **Use Type Hints** - Enables automatic schema generation
2. **Return JSON Strings** - Consistent format across modes
3. **Handle Errors Gracefully** - Return error objects, don't raise
4. **Document Tools** - Use docstrings for descriptions
5. **Keep Tools Simple** - One responsibility per tool

## Troubleshooting

### Lambda Mode Issues

**Tool not discovered:**
- Check Lambda function name in FUNCTION_LIST
- Verify discovery response format
- Check CloudWatch logs

**Tool invocation fails:**
- Verify argument names match schema
- Check tool name is correct
- Review Lambda execution logs

### Standalone Mode Issues

**Server won't start:**
- Check Python version (3.10+)
- Verify chuk-mcp-server is installed
- Check for port conflicts

**MCP client can't connect:**
- Verify command path in config
- Check stdio transport is working
- Review client logs

## Next Steps

1. Study the code in `app.py`
2. Try running in both modes
3. Add your own custom tools
4. Deploy to Lambda and test with shepp-lambda-mcp
5. Use as a template for your own dual-mode functions

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License, Version 2.0.
