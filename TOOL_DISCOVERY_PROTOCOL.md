# Tool Discovery Protocol for Lambda MCP Server

## Overview

This document describes the tool discovery protocol that allows Lambda functions to expose multiple MCP tools instead of being limited to one tool per function.

## Protocol Design

### Discovery Phase (Server Initialization)

When the MCP server initializes, it will:

1. Call each configured Lambda function with a special discovery payload
2. Parse the response to extract tool definitions
3. Register each tool as a separate MCP tool

### Discovery Request Format

```json
{
  "action": "discover_tools"
}
```

### Discovery Response Format

The Lambda function must return a JSON response with the following structure:

```json
{
  "tools": [
    {
      "name": "tool_name",
      "description": "Detailed description of what this tool does",
      "inputSchema": {
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "description": "Description of param1"
          },
          "param2": {
            "type": "integer",
            "description": "Description of param2",
            "default": 5
          }
        },
        "required": ["param1"]
      }
    }
  ]
}
```

### Tool Invocation Format

When invoking a specific tool, the MCP server will call the Lambda function with:

```json
{
  "tool": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": 10
  }
}
```

Or for backward compatibility with the flat format:

```json
{
  "tool": "tool_name",
  "param1": "value1",
  "param2": 10
}
```

## Lambda Function Implementation

### Handler Structure

Lambda functions should implement a handler that:

1. Checks for the `action` field
2. If `action == "discover_tools"`, returns tool definitions
3. Otherwise, routes to the appropriate tool handler based on the `tool` field

### Example Implementation

```python
def lambda_handler(event, context):
    # Discovery request
    if event.get("action") == "discover_tools":
        return {
            "tools": [
                {
                    "name": "race_vector_search",
                    "description": "Search race information and press releases",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 5},
                            "language": {"type": "string", "description": "Language code", "default": "EN"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "team_vector_search",
                    "description": "Search team profiles and driver information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 5},
                            "language": {"type": "string", "description": "Language code", "default": "EN"}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    
    # Tool invocation
    tool_name = event.get("tool")
    arguments = event.get("arguments", {k: v for k, v in event.items() if k != "tool"})
    
    if tool_name == "race_vector_search":
        return race_vector_search(arguments)
    elif tool_name == "team_vector_search":
        return team_vector_search(arguments)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown tool: {tool_name}"})
        }
```

## Backward Compatibility

For Lambda functions that don't implement the discovery protocol:

1. If the discovery call fails or returns an unexpected format, fall back to the old behavior
2. Create a single tool using the Lambda function name and description
3. Log a warning about the legacy mode

## Benefits

1. **Multiple Tools per Function**: One Lambda can expose many related tools
2. **Better Documentation**: Each tool has its own description and schema
3. **Cleaner Separation**: Tool logic is separated from MCP protocol handling
4. **Type Safety**: Input schemas provide validation and better IDE support
5. **Flexibility**: Lambda functions can dynamically generate tool lists

## Migration Path

1. Update the MCP server to support the discovery protocol
2. Update Lambda functions to implement the protocol
3. Maintain backward compatibility for existing functions
4. Gradually migrate functions to the new protocol
