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

### New Multi-Tool Function (Tool Discovery)

**CustomerManagement** - A single Lambda function that exposes **4 tools** using the tool discovery protocol:

1. `get_customer_info` - Retrieve customer information by ID
2. `get_customer_id_from_email` - Look up customer ID by email
3. `create_customer` - Create a new customer account
4. `update_customer` - Update existing customer information

This demonstrates how one Lambda function can provide multiple related tools, each with:
- Detailed descriptions
- JSON Schema for input validation
- Type-safe parameters

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

## MCP Server Configuration

To use these functions with the MCP server, add them to your configuration:

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
- `CustomerManagementFunction_get_customer_info`
- `CustomerManagementFunction_get_customer_id_from_email`
- `CustomerManagementFunction_create_customer`
- `CustomerManagementFunction_update_customer`

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