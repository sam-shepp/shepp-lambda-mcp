# Shepp Lambda MCP Server

A Model Context Protocol (MCP) server for AWS Lambda to select and run Lambda function as MCP tools without code changes.

**Note**: This is a fork with enhanced authentication flexibility - AWS profile is optional, you can use direct AWS credentials instead.

## Features

This MCP server acts as a **bridge** between MCP clients and AWS Lambda functions, allowing generative AI models to access and run Lambda functions as tools. This is useful, for example, to access private resources such as internal applications and databases without the need to provide public network access. This approach allows the model to use other AWS services, private networks, and the public internet.

### Tool Discovery Protocol (New in v2.1.0)

Lambda functions can now expose **multiple tools** instead of being limited to one tool per function. The server implements a discovery protocol that:

1. **Discovers Tools at Startup**: When the MCP server initializes, it calls each Lambda function with `{"action": "discover_tools"}` to get a list of available tools
2. **Registers Multiple Tools**: Each discovered tool is registered as a separate MCP tool with its own name, description, and input schema
3. **Backward Compatible**: Functions that don't implement the discovery protocol continue to work as before (one tool per function)

**Benefits:**
- One Lambda function can provide multiple related tools (e.g., different search types)
- Better tool documentation with detailed descriptions and JSON schemas
- Cleaner separation of concerns within Lambda functions
- Type-safe tool parameters with schema validation

See [TOOL_DISCOVERY_PROTOCOL.md](TOOL_DISCOVERY_PROTOCOL.md) for implementation details.

```mermaid
graph LR
    A[Model] <--> B[MCP Client]
    B <--> C["MCP2Lambda<br>(MCP Server)"]
    C <--> D[Lambda Function]
    D <--> E[Other AWS Services]
    D <--> F[Internet]
    D <--> G[VPC]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:4px
    style D fill:#fbb,stroke:#333,stroke-width:2px
    style E fill:#fbf,stroke:#333,stroke-width:2px
    style F fill:#dff,stroke:#333,stroke-width:2px
    style G fill:#ffd,stroke:#333,stroke-width:2px
```

From a **security** perspective, this approach implements segregation of duties by allowing the model to invoke the Lambda functions but not to access the other AWS services directly. The client only needs AWS credentials to invoke the Lambda functions. The Lambda functions can then interact with other AWS services (using the function role) and access public or private networks.

## Prerequisites

1. Install `uv` from [Astral](https://docs.astral.sh/uv/getting-started/installation/) or the [GitHub README](https://github.com/astral-sh/uv#installation)
2. Install Python using `uv python install 3.11`

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
uvx shepp-lambda-mcp
```

Or install in your project:

```bash
uv pip install shepp-lambda-mcp
```

### Option 2: Install from GitHub

```bash
uvx --from git+https://github.com/sam-shepp/shepp-lambda-mcp shepp-lambda-mcp
```

## Configuration



Configure the MCP server in your MCP client configuration (e.g., for Kiro, edit `~/.kiro/settings/mcp.json`).

### Option 1: Using AWS Profile (Optional - for local development)

```json
{
  "mcpServers": {
    "shepp-lambda-mcp": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1",
        "FUNCTION_PREFIX": "your-function-prefix",
        "FUNCTION_LIST": "your-first-function, your-second-function",
        "FUNCTION_TAG_KEY": "your-tag-key",
        "FUNCTION_TAG_VALUE": "your-tag-value",
        "FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY": "your-function-tag-for-input-schema"
      }
    }
  }
}
```

### Option 2: Using Direct AWS Credentials (Recommended for flexibility)

You can pass AWS credentials directly without using a profile. This is now the preferred method as it provides more flexibility:

```json
{
  "mcpServers": {
    "shepp-lambda-mcp": {
      "command": "uvx",
      "args": ["shepp-lambda-mcp"],
      "env": {
        "AWS_ACCESS_KEY_ID": "your-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-secret-access-key",
        "AWS_SESSION_TOKEN": "your-session-token",
        "AWS_REGION": "us-east-1",
        "FUNCTION_PREFIX": "your-function-prefix",
        "FUNCTION_LIST": "your-first-function, your-second-function",
        "FUNCTION_TAG_KEY": "your-tag-key",
        "FUNCTION_TAG_VALUE": "your-tag-value",
        "FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY": "your-function-tag-for-input-schema"
      }
    }
  }
}
```

**Note**: `AWS_SESSION_TOKEN` is optional and only required for temporary credentials (e.g., from AWS STS).

### Windows Installation

For Windows users, the MCP server configuration format is slightly different:

```json
{
  "mcpServers": {
    "shepp-lambda-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uvx",
      "args": [
        "shepp-lambda-mcp"
      ],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1",
        "FUNCTION_PREFIX": "your-function-prefix",
        "FUNCTION_LIST": "your-first-function, your-second-function",
        "FUNCTION_TAG_KEY": "your-tag-key",
        "FUNCTION_TAG_VALUE": "your-tag-value",
        "FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY": "your-function-tag-for-input-schema"
      }
    }
  }
}
```

or docker after a successful `docker build -t awslabs/bedrock-kb-retrieval-mcp-server .`:

```file
# fictitious `.env` file with AWS temporary credentials
AWS_ACCESS_KEY_ID=ASIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_SESSION_TOKEN=AQoEXAMPLEH4aoAH0gNCAPy...truncated...zrkuWJOgQs8IZZaIv2BXIa2R4Olgk
```

```json
  {
    "mcpServers": {
      "shepp-lambda-mcp": {
        "command": "docker",
        "args": [
          "run",
          "--rm",
          "--interactive",
          "--env",
          "AWS_REGION=us-east-1",
          "--env",
          "FUNCTION_PREFIX=your-function-prefix",
          "--env",
          "FUNCTION_LIST=your-first-function,your-second-function",
          "--env",
          "FUNCTION_TAG_KEY=your-tag-key",
          "--env",
          "FUNCTION_TAG_VALUE=your-tag-value",
          "--env",
          "FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY=your-function-tag-for-input-schema",
          "--env-file",
          "/full/path/to/file/above/.env",
          "shepp-lambda-mcp:latest"
        ],
        "env": {},
        "disabled": false,
        "autoApprove": []
      }
    }
  }
```

NOTE: Your credentials will need to be kept refreshed from your host

## AWS Authentication

**Important**: AWS Profile is now optional! The server supports multiple authentication methods with the following priority:

1. **Direct Credentials** (highest priority, recommended): Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN`
2. **AWS Profile** (optional): Set `AWS_PROFILE` to use a named profile from your AWS credentials file
3. **Default Credentials Chain** (lowest priority): Uses the standard AWS SDK credential resolution (environment variables, EC2 instance profile, etc.)

The `AWS_REGION` defaults to `us-east-1` if not specified.

**Note**: You can now use this server without configuring an AWS profile - simply provide your access keys directly in the configuration.

You can specify `FUNCTION_PREFIX`, `FUNCTION_LIST`, or both. If both are empty, all functions pass the name check.
After the name check, if both `FUNCTION_TAG_KEY` and `FUNCTION_TAG_VALUE` are set, functions are further filtered by tag (with key=value).
If only one of `FUNCTION_TAG_KEY` and `FUNCTION_TAG_VALUE`, then no function is selected and a warning is displayed.

### Tool Naming and Discovery

**With Tool Discovery (v2.1.0+):**
- Lambda functions can expose multiple tools by implementing the discovery protocol
- Each tool has its own name, description, and input schema
- Tool names are used directly as defined in the Lambda function (e.g., `race_vector_search`)
- See [TOOL_DISCOVERY_PROTOCOL.md](TOOL_DISCOVERY_PROTOCOL.md) for implementation details

**Legacy Mode (Backward Compatible):**
- The function name is used as the MCP tool name
- The function description in AWS Lambda is used as the MCP tool description
- The function description should clarify when to use the function (what it provides) and how (which parameters)
- Example: A function that gives access to an internal CRM system can use this description:
  ```plaintext
  Retrieve customer status on the CRM system based on { 'customerId' } or { 'customerEmail' }
  ```
- Lambda function parameters can also be provided through the EventBridge Schema Registry (see [Schema Support](#schema-support))

Sample functions that can be deployed via AWS SAM are provided in the `examples` folder.

## Schema Support

The Lambda MCP Server supports input schema through AWS EventBridge Schema Registry. This provides formal JSON Schema documentation for your Lambda function inputs.

### Configuration

To use schema validation:

1. Create your schema in EventBridge Schema Registry
2. Tag your Lambda function with the schema ARN:
   ```plaintext
   Key: FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY (configurable)
   Value: arn:aws:schemas:region:account:schema/registry-name/schema-name
   ```
3. Configure the MCP server with the tag key:
   ```json
   {
     "env": {
       "FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY": "your-schema-arn-tag-key"
     }
   }
   ```

When a Lambda function has a schema tag, the MCP server will:
1. Fetch the schema from EventBridge Schema Registry
2. Add the schema to the tool's documentation

This provides better documentation compared to describing parameters in the function description.

## Best practices

- Use the `FUNCTION_LIST` to specify the functions that are available as MCP tools.
- Use the `FUNCTION_PREFIX` to specify the prefix of the functions that are available as MCP tools.
- Use the `FUNCTION_TAG_KEY` and `FUNCTION_TAG_VALUE` to specify the tag key and value of the functions that are available as MCP tools.
- AWS Lambda `Description` property: the description of the function is used as MCP tool description, so it should be very detailed to help the model understand when and how to use the function
- Use EventBridge Schema Registry to provide formal input validation:
  - Create JSON Schema definitions for your function inputs
  - Tag functions with their schema ARNs
  - Configure `FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY` in the MCP server

## Security Considerations

When using this MCP server, you should consider:

- Only Lambda functions that are in the provided list or with a name starting with the prefix are imported as MCP tools.
- The MCP server needs permissions to invoke the Lambda functions.
- Each Lambda function has its own permissions to optionally access other AWS resources.
