# Simple Tools MCP - Dual-Mode Lambda/MCP Server

A **production-ready** Lambda function that can operate in **two modes**:
1. **Lambda Mode**: Deploy to AWS Lambda, invoked via shepp-lambda-mcp
2. **Standalone Mode**: Run directly as an MCP server with any MCP client

## 🌟 Key Features

✅ **Dual-Mode Operation** - Works as Lambda function OR standalone MCP server  
✅ **Proper Package Structure** - Full Python package with src/, tests/, pyproject.toml  
✅ **ChukMCPServer** - Uses chuk-mcp-server package for MCP functionality  
✅ **Portable** - Same code runs anywhere (Lambda, local, container, VM)  
✅ **Type-Safe** - Python type hints throughout  
✅ **Tested** - Comprehensive test suite with pytest  
✅ **Production-Ready** - Proper logging, error handling, and packaging  

## 📦 Package Structure

```
simple-tools-mcp/
├── src/
│   └── simple_tools_mcp/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # MCP server entry point
│       ├── lambda_handler.py    # AWS Lambda handler
│       └── tools.py             # Tool implementations
├── tests/
│   ├── __init__.py
│   ├── test_tools.py           # Tool tests
│   └── test_lambda_handler.py  # Lambda handler tests
├── examples/
│   ├── lambda_config.json      # Lambda mode config
│   └── standalone_config.json  # Standalone mode config
├── pyproject.toml              # Package configuration
├── Makefile                    # Development commands
├── README.md                   # This file
└── .gitignore                  # Git ignore patterns
```

## 🚀 Quick Start

### Installation

**For standalone use:**
```bash
pip install -e .
```

**For development:**
```bash
pip install -e ".[dev]"
```

**Using uv (recommended):**
```bash
uv pip install -e .
```

### Running as Standalone MCP Server

**Option 1: Using the installed command**
```bash
simple-tools-mcp
```

**Option 2: Using Python module**
```bash
python -m simple_tools_mcp.server
```

**Option 3: Using Makefile**
```bash
make run-local
```

### Deploying to AWS Lambda

**1. Build and deploy with SAM:**
```bash
cd ..  # Go to sample_functions directory
sam build
sam deploy
```

**2. Configure shepp-lambda-mcp:**
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

## 🛠️ Available Tools

### 1. hello_world
Simple greeting with optional name parameter.

**Parameters:**
- `name` (string, optional): Name to greet. Defaults to "World"

**Example:**
```json
{
  "tool": "hello_world",
  "arguments": {"name": "Alice"}
}
```

### 2. echo
Echo messages with uppercase and repeat formatting options.

**Parameters:**
- `message` (string, required): Message to echo
- `uppercase` (boolean, optional): Convert to uppercase. Defaults to false
- `repeat` (integer, optional): Repeat count (1-10). Defaults to 1

**Example:**
```json
{
  "tool": "echo",
  "arguments": {
    "message": "hello",
    "uppercase": true,
    "repeat": 3
  }
}
```

### 3. get_timestamp
Get current timestamp in various formats.

**Parameters:**
- `format` (string, optional): Format type - "iso", "unix", or "readable". Defaults to "iso"
- `timezone` (string, optional): Timezone name. Defaults to "UTC"

**Example:**
```json
{
  "tool": "get_timestamp",
  "arguments": {"format": "readable"}
}
```

### 4. calculate
Basic arithmetic operations.

**Parameters:**
- `operation` (string, required): Operation - "add", "subtract", "multiply", or "divide"
- `a` (number, required): First operand
- `b` (number, required): Second operand

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

## 🧪 Testing

**Run all tests:**
```bash
make test
```

**Or using pytest directly:**
```bash
pytest tests/ -v
```

**With coverage:**
```bash
pytest tests/ -v --cov=simple_tools_mcp --cov-report=term-missing
```

## 🔍 Development

**Format code:**
```bash
make format
```

**Lint code:**
```bash
make lint
```

**Clean build artifacts:**
```bash
make clean
```

**Build package:**
```bash
make build
```

## 📋 Usage Examples

### As Standalone MCP Server

**1. Install the package:**
```bash
pip install -e .
```

**2. Configure your MCP client (e.g., Bob Shell):**
```json
{
  "mcpServers": {
    "simple-tools": {
      "command": "simple-tools-mcp",
      "args": []
    }
  }
}
```

**3. Use the tools in your MCP client:**
- All 4 tools will be available
- Tools are registered automatically via @tool decorators
- Full MCP protocol support (list_tools, call_tool)

### As AWS Lambda Function

**1. Deploy to Lambda:**
```bash
cd ..  # sample_functions directory
sam build
sam deploy
```

**2. Test discovery:**
```bash
aws lambda invoke \
  --function-name SimpleToolsMCPFunction \
  --payload '{"action": "discover_tools"}' \
  response.json
```

**3. Test tool invocation:**
```bash
aws lambda invoke \
  --function-name SimpleToolsMCPFunction \
  --payload '{"tool": "hello_world", "arguments": {"name": "Lambda"}}' \
  response.json
```

**4. Use with shepp-lambda-mcp:**
```json
{
  "mcpServers": {
    "simple-tools-lambda": {
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

## 🏗️ Architecture

### Dual-Mode Design

The package uses a clean separation of concerns:

**1. Tools (`tools.py`)**
- Pure tool implementations
- Decorated with `@tool` from chuk-mcp-server
- No Lambda or MCP-specific code
- Fully testable in isolation

**2. MCP Server (`server.py`)**
- Entry point for standalone mode
- Imports tools to register them
- Runs ChukMCPServer with stdio transport
- Handles command-line arguments

**3. Lambda Handler (`lambda_handler.py`)**
- Entry point for Lambda mode
- Implements tool discovery protocol
- Routes tool invocations to registered tools
- Returns JSON responses

### How It Works

**Standalone Mode:**
```
MCP Client → stdio → server.py → ChukMCPServer → tools.py
```

**Lambda Mode:**
```
shepp-lambda-mcp → Lambda invoke → lambda_handler.py → tools.py
```

Both modes use the **same tool implementations** from `tools.py`.

## 🎯 Benefits of This Pattern

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
- Proper package structure

### 4. **Cost Optimization**
- Use Lambda for production (pay per use)
- Use local/container for development (free)
- Choose deployment based on needs

### 5. **Production Ready**
- Proper Python package structure
- Comprehensive test suite
- Type hints throughout
- Logging and error handling

## 📝 Creating Your Own Dual-Mode Server

Use this as a template:

**1. Copy the structure:**
```bash
cp -r simple-tools-mcp my-tools-mcp
cd my-tools-mcp
```

**2. Update package name in `pyproject.toml`:**
```toml
[project]
name = "my-tools-mcp"
```

**3. Add your tools in `src/my_tools_mcp/tools.py`:**
```python
from chuk_mcp_server import tool

@tool(name='my_tool')
def my_tool(param: str) -> str:
    """Your tool implementation."""
    return json.dumps({"result": param})
```

**4. Update imports in `server.py` and `lambda_handler.py`**

**5. Install and test:**
```bash
pip install -e .
my-tools-mcp  # Run standalone
```

## 🐛 Troubleshooting

### Standalone Mode Issues

**Server won't start:**
- Check Python version (3.11+)
- Verify chuk-mcp-server is installed: `pip list | grep chuk-mcp-server`
- Check for port conflicts

**MCP client can't connect:**
- Verify command path in config
- Check stdio transport is working
- Review client logs

### Lambda Mode Issues

**Tool not discovered:**
- Check Lambda function name in FUNCTION_LIST
- Verify discovery response format
- Check CloudWatch logs

**Tool invocation fails:**
- Verify argument names match schema
- Check tool name is correct
- Review Lambda execution logs

## 📚 Additional Resources

- [ChukMCPServer Documentation](https://github.com/chrishayuk/chuk-mcp-server)
- [shepp-lambda-mcp Documentation](https://github.com/samsheppard/shepp-lambda-mcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io)

## 📄 License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License, Version 2.0.