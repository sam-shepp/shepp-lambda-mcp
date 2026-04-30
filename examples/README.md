# MCP Server Sample Lambda Functions

This directory contains sample Lambda functions that demonstrate different use cases for the MCP server. These functions are designed to be deployed using the AWS SAM CLI.

## Tool Discovery Protocol (v2.1.0+)

The examples now include both **legacy single-tool functions** and a **new multi-tool function** that demonstrates the tool discovery protocol.

### Legacy Functions (Backward Compatibility)

The first three functions demonstrate the original approach where each Lambda function exposes a single tool:

1. **CustomerInfoFromId** - Retrieves customer information by ID
2. **CustomerIdFromEmail** - Looks up customer ID by email
3. **CustomerCreate** - Creates a new customer account

These functions continue to work with the MCP server for backward compatibility.

### New Multi-Tool Functions (Tool Discovery)

#### CustomerManagement

A single Lambda function that exposes **4 tools** using the tool discovery protocol:

1. `get_customer_info` - Retrieve customer information by ID
2. `get_customer_id_from_email` - Look up customer ID by email
3. `create_customer` - Create a new customer account
4. `update_customer` - Update existing customer information

This demonstrates how one Lambda function can provide multiple related tools, each with:
- Detailed descriptions
- JSON Schema for input validation
- Type-safe parameters

#### SimpleTools

A beginner-friendly Lambda function that exposes **4 simple tools** perfect for learning the tool discovery protocol:

1. `hello_world` - Simple greeting tool with optional name parameter
2. `echo` - Echo messages with optional uppercase and repeat formatting
3. `get_timestamp` - Get current timestamp in various formats (ISO, Unix, readable)
4. `calculate` - Perform basic arithmetic operations (add, subtract, multiply, divide)

This is the **recommended starting point** for learning how to implement the tool discovery protocol. Each tool demonstrates:
- Clear, simple functionality
- Proper input validation
- Comprehensive error handling
- Well-documented schemas

#### SimpleToolsMCP (Dual-Mode Pattern) ⭐ **RECOMMENDED**

A **dual-mode Lambda/MCP server** that can operate in two ways:
1. **As a Lambda function** - Deploy to AWS Lambda, invoke via shepp-lambda-mcp
2. **As a standalone MCP server** - Run directly with any MCP client

**Key Benefits:**
- ✅ **Portable** - Same code runs anywhere (Lambda, local, container, VM)
- ✅ **Flexible** - Choose deployment based on needs (serverless vs local)
- ✅ **Developer-Friendly** - Test locally without AWS, debug with standard tools
- ✅ **Cost-Effective** - Use Lambda for production, local for development
- ✅ **ChukMCPServer** - Uses chuk-mcp-server package for MCP functionality

**Tools Exposed:**
1. `hello_world` - Simple greeting with optional name parameter
2. `echo` - Echo messages with formatting options
3. `get_timestamp` - Get current timestamp in various formats
4. `calculate` - Basic arithmetic operations

This is the **recommended pattern** for building Lambda functions that are also MCP servers. See `simple-tools-mcp/README.md` for detailed documentation.

## Available Functions

### Legacy Functions

#### 1. CustomerInfoFromId

- **Purpose**: Retrieves customer status information using a customer ID
- **Input**: `{ "customerId": "string" }`
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64

#### 2. CustomerIdFromEmail

- **Purpose**: Looks up a customer ID using an email address
- **Input**: `{ "email": "string" }`
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64

#### 3. CustomerCreate

- **Purpose**: Creates a new customer account
- **Input**: `{ "name": "string", "email": "string", "phone": "string", "address": {...} }`
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64

### Multi-Tool Function (Tool Discovery)

#### 4. CustomerManagement

- **Purpose**: Comprehensive customer management with multiple tools
- **Tools Exposed**:
  - `get_customer_info` - Get customer details by ID
  - `get_customer_id_from_email` - Find customer ID from email
  - `create_customer` - Create new customer
  - `update_customer` - Update customer information
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64
- **Tags**: `MCP: enabled`, `ToolDiscovery: v2.1.0`

#### 5. SimpleTools (Recommended for Learning)

- **Purpose**: Simple example tools for learning the tool discovery protocol
- **Tools Exposed**:
  - `hello_world` - Simple greeting with optional name
  - `echo` - Echo messages with formatting options
  - `get_timestamp` - Get current time in various formats
  - `calculate` - Basic arithmetic operations
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64
- **Tags**: `MCP: enabled`, `ToolDiscovery: v2.1.0`, `Example: basic`

#### 6. SimpleToolsMCP (Dual-Mode Pattern - Recommended)

- **Purpose**: **Dual-mode Lambda/MCP server** - can run as Lambda function OR standalone MCP server
- **Tools Exposed**:
  - `hello_world` - Simple greeting with optional name
  - `echo` - Echo messages with formatting options
  - `get_timestamp` - Get current time in various formats
  - `calculate` - Basic arithmetic operations
- **Key Features**:
  - Uses `ChukMCPServer` package
  - Same code runs as Lambda or standalone
  - Can be deployed to Lambda AND run locally
  - Perfect template for building portable MCP tools
- **Memory**: 128 MB
- **Timeout**: 3 seconds
- **Runtime**: Python 3.13
- **Architecture**: ARM64
- **Tags**: `MCP: enabled`, `ToolDiscovery: v2.1.0`, `Example: dual-mode`, `ChukMCPServer: true`

## Tool Discovery Protocol

The CustomerManagement function demonstrates the tool discovery protocol:

1. **Discovery Request**: MCP server sends `{"action": "discover_tools"}` during initialization
2. **Discovery Response**: Function returns tool definitions with schemas
3. **Tool Invocation**: MCP server calls with `{"tool": "tool_name", "arguments": {...}}`

Example discovery response:
```json
{
  "tools": [
    {
      "name": "get_customer_info",
      "description": "Retrieve detailed customer information...",
      "inputSchema": {
        "type": "object",
        "properties": {
          "customerId": {"type": "string", "description": "..."}
        },
        "required": ["customerId"]
      }
    }
  ]
}
```

## Installation

### Prerequisites

1. Install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
2. Configure AWS credentials with appropriate permissions
3. Python 3.13 installed locally (for local testing)

### Deployment Steps

1. Navigate to the sample functions directory:

   ```bash
   cd examples/sample_functions
   ```

2. Build the application:

   ```bash
   sam build
   ```

3. Deploy the application:

   ```bash
   sam deploy --guided
   ```

   During the guided deployment, you'll be prompted to:
   - Choose a stack name
   - Select an AWS Region
   - Confirm IAM role creation
   - Allow SAM CLI to create IAM roles
   - Save arguments to samconfig.toml

4. For subsequent deployments, you can use:

   ```bash
   sam deploy
   ```

## Testing Tool Discovery

After deployment, you can test the tool discovery protocol:

### Testing CustomerManagement Function

1. **Test Discovery**:
   ```bash
   aws lambda invoke \
     --function-name CustomerManagementFunction \
     --payload '{"action": "discover_tools"}' \
     response.json
   cat response.json
   ```

2. **Test Tool Invocation**:
   ```bash
   aws lambda invoke \
     --function-name CustomerManagementFunction \
     --payload '{"tool": "get_customer_info", "arguments": {"customerId": "12345"}}' \
     response.json
   cat response.json
   ```

### Testing SimpleTools Function (Recommended for Beginners)

1. **Test Discovery**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsFunction \
     --payload '{"action": "discover_tools"}' \
     response.json
   cat response.json
   ```

2. **Test hello_world**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsFunction \
     --payload '{"tool": "hello_world", "arguments": {"name": "Alice"}}' \
     response.json
   cat response.json
   ```

3. **Test echo**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsFunction \
     --payload '{"tool": "echo", "arguments": {"message": "Hello MCP", "uppercase": true, "repeat": 3}}' \
     response.json
   cat response.json
   ```

4. **Test get_timestamp**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsFunction \
     --payload '{"tool": "get_timestamp", "arguments": {"format": "readable"}}' \
     response.json
   cat response.json
   ```

5. **Test calculate**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsFunction \
     --payload '{"tool": "calculate", "arguments": {"operation": "multiply", "a": 7, "b": 6}}' \
     response.json
   cat response.json
   ```

### Testing SimpleToolsMCP Function (Dual-Mode)

#### As Lambda Function

1. **Test Discovery**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsMCPFunction \
     --payload '{"action": "discover_tools"}' \
     response.json
   cat response.json
   ```

2. **Test hello_world**:
   ```bash
   aws lambda invoke \
     --function-name SimpleToolsMCPFunction \
     --payload '{"tool": "hello_world", "arguments": {"name": "Bob"}}' \
     response.json
   cat response.json
   ```

#### As Standalone MCP Server

1. **Install dependencies**:
   ```bash
   cd simple-tools-mcp
   pip install -r requirements.txt
   ```

2. **Run as MCP server**:
   ```bash
   python app.py
   ```

3. **Configure MCP client** (e.g., Bob Shell):
   ```json
   {
     "mcpServers": {
       "simple-tools-local": {
         "command": "python",
         "args": ["/absolute/path/to/simple-tools-mcp/app.py"]
       }
     }
   }
   ```

4. **Test with MCP client** - The server will be available with all 4 tools

## MCP Server Configuration

To use these functions with the MCP server, add them to your configuration:

### Using CustomerManagement Function

```json
{
  "mcpServers": {
    "customer-management": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FUNCTION_LIST": "CustomerManagementFunction"
      }
    }
  }
}
```

The MCP server will automatically discover all 4 tools from the CustomerManagementFunction and register them as:
- `get_customer_info`
- `get_customer_id_from_email`
- `create_customer`
- `update_customer`

### Using SimpleTools Function (Recommended for Learning)

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

The MCP server will automatically discover all 4 tools from the SimpleToolsFunction and register them as:
- `hello_world`
- `echo`
- `get_timestamp`
- `calculate`

### Using Both Functions

```json
{
  "mcpServers": {
    "lambda-tools": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "FUNCTION_LIST": "CustomerManagementFunction,SimpleToolsFunction"
      }
    }
  }
}
```

This will register all 8 tools from both functions.

### Using SimpleToolsMCP (Dual-Mode - Recommended)

**As Lambda Function:**
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

**As Standalone MCP Server:**
```json
{
  "mcpServers": {
    "simple-tools-local": {
      "command": "python",
      "args": ["/absolute/path/to/simple-tools-mcp/app.py"]
    }
  }
}
```

**Both modes register the same 4 tools:**
- `hello_world`
- `echo`
- `get_timestamp`
- `calculate`

The dual-mode pattern gives you flexibility to choose the best deployment for your needs.

## Cleanup

To remove all deployed resources:

```bash
sam delete --stack-name <your-stack-name>
```

## Security Considerations

- All functions run on ARM64 architecture for cost optimization
- The default IAM role permissions are used
- Review and adjust memory and timeout settings based on your specific needs
- Consider adding authentication and authorization for production use

## Migration Guide

To migrate existing single-tool functions to the multi-tool pattern:

1. Implement `get_tool_definitions()` function returning tool schemas
2. Add tool routing logic in `lambda_handler()`
3. Support both `{"action": "discover_tools"}` and tool invocation formats
4. Test with the MCP server to verify all tools are discovered
5. Maintain backward compatibility by supporting legacy parameter formats

See `customer-management/app.py` for a complete implementation example.