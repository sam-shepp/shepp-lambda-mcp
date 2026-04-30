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

"""awslabs lambda MCP Server implementation using ChukMCPServer with tool discovery."""

import boto3
import json
import logging
import os
import re
from chuk_mcp_server import ChukMCPServer
from typing import Optional, Dict, List, Any


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1')
logger.info(f'AWS_REGION: {AWS_REGION}')

# AWS Credentials - can be provided directly or via profile
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')
AWS_PROFILE = os.environ.get('AWS_PROFILE')

# Log which authentication method is being used (without exposing credentials)
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    logger.info('Using AWS credentials from environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)')
    if AWS_SESSION_TOKEN:
        logger.info('AWS_SESSION_TOKEN is also provided')
elif AWS_PROFILE:
    logger.info(f'Using AWS profile: {AWS_PROFILE}')
else:
    logger.info('Using default AWS credentials chain')

FUNCTION_PREFIX = os.environ.get('FUNCTION_PREFIX', '')
logger.info(f'FUNCTION_PREFIX: {FUNCTION_PREFIX}')

FUNCTION_LIST = [
    function_name.strip()
    for function_name in os.environ.get('FUNCTION_LIST', '').split(',')
    if function_name.strip()
]
logger.info(f'FUNCTION_LIST: {FUNCTION_LIST}')

FUNCTION_TAG_KEY = os.environ.get('FUNCTION_TAG_KEY', '')
logger.info(f'FUNCTION_TAG_KEY: {FUNCTION_TAG_KEY}')

FUNCTION_TAG_VALUE = os.environ.get('FUNCTION_TAG_VALUE', '')
logger.info(f'FUNCTION_TAG_VALUE: {FUNCTION_TAG_VALUE}')

FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY = os.environ.get('FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY')
logger.info(f'FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY: {FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY}')

# Initialize AWS clients with credentials
# Priority: Direct credentials > Profile > Default credentials chain
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # Use explicit credentials
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=AWS_REGION
    )
elif AWS_PROFILE:
    # Use profile
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
else:
    # Use default credentials chain (environment variables, instance profile, etc.)
    session = boto3.Session(region_name=AWS_REGION)

lambda_client = session.client('lambda')
schemas_client = session.client('schemas')

mcp = ChukMCPServer(
    name='shepp-lambda-mcp',
    version='2.0.17',
    description="""Use AWS Lambda functions to improve your answers.
    These Lambda functions give you additional capabilities and access to AWS services and resources in an AWS account.""",
    transport='stdio',
)


def validate_function_name(function_name: str) -> bool:
    """Validate that the function name is valid and can be called."""
    # If both prefix and list are empty, consider all functions valid
    if not FUNCTION_PREFIX and not FUNCTION_LIST:
        return True

    # Otherwise, check if the function name matches the prefix or is in the list
    return (FUNCTION_PREFIX and function_name.startswith(FUNCTION_PREFIX)) or (
        function_name in FUNCTION_LIST
    )


def sanitize_tool_name(name: str) -> str:
    """Sanitize a tool name to be used as an MCP tool name."""
    # Replace invalid characters with underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

    # Ensure name doesn't start with a number
    if name and name[0].isdigit():
        name = '_' + name

    return name


def format_lambda_response(function_name: str, tool_name: str, payload: bytes) -> str:
    """Format the Lambda function response payload."""
    try:
        # Try to parse the payload as JSON
        payload_json = json.loads(payload)
        return f'Tool {tool_name} (function {function_name}) returned: {json.dumps(payload_json, indent=2)}'
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Return raw payload if not JSON
        return f'Tool {tool_name} (function {function_name}) returned payload: {payload}'


def discover_tools_from_lambda(function_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Discover tools from a Lambda function by calling it with a discovery payload.
    
    Args:
        function_name: Name of the Lambda function
        
    Returns:
        List of tool definitions or None if discovery fails
    """
    try:
        logger.info(f'Discovering tools from Lambda function: {function_name}')
        
        # Call Lambda with discovery payload
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'discover_tools'}),
        )
        
        if 'FunctionError' in response:
            logger.warning(f'Function {function_name} returned error during discovery: {response["FunctionError"]}')
            return None
        
        payload = response['Payload'].read()
        result = json.loads(payload)
        
        # Check if response has tools array
        if isinstance(result, dict) and 'tools' in result:
            tools = result['tools']
            logger.info(f'Discovered {len(tools)} tools from function {function_name}')
            return tools
        else:
            logger.warning(f'Function {function_name} did not return expected discovery format')
            return None
            
    except Exception as e:
        logger.warning(f'Error discovering tools from function {function_name}: {e}')
        return None


async def invoke_lambda_tool_impl(function_name: str, tool_name: str, parameters: dict) -> str:
    """
    Invoke a specific tool within a Lambda function.
    
    Args:
        function_name: Name of the Lambda function
        tool_name: Name of the tool to invoke
        parameters: Tool parameters
        
    Returns:
        Tool execution result
    """
    logger.info(f'Invoking tool {tool_name} in function {function_name} with parameters: {parameters}')

    # Build payload with tool name and arguments
    payload = {
        'tool': tool_name,
        'arguments': parameters
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload),
    )

    logger.info(f'Tool {tool_name} in function {function_name} returned with status code: {response["StatusCode"]}')

    if 'FunctionError' in response:
        error_message = (
            f'Tool {tool_name} in function {function_name} returned with error: {response["FunctionError"]}'
        )
        logger.error(error_message)
        return error_message

    payload_bytes = response['Payload'].read()
    # Format the response payload
    return format_lambda_response(function_name, tool_name, payload_bytes)


async def invoke_lambda_function_impl(function_name: str, parameters: dict) -> str:
    """
    Legacy tool invocation for Lambda functions that don't support tool discovery.
    
    Args:
        function_name: Name of the Lambda function
        parameters: Function parameters
        
    Returns:
        Function execution result
    """
    logger.info(f'Invoking legacy function {function_name} with parameters: {parameters}')

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(parameters),
    )

    logger.info(f'Function {function_name} returned with status code: {response["StatusCode"]}')

    if 'FunctionError' in response:
        error_message = (
            f'Function {function_name} returned with error: {response["FunctionError"]}'
        )
        logger.error(error_message)
        return error_message

    payload = response['Payload'].read()
    # Format the response payload
    try:
        payload_json = json.loads(payload)
        return f'Function {function_name} returned: {json.dumps(payload_json, indent=2)}'
    except (json.JSONDecodeError, UnicodeDecodeError):
        return f'Function {function_name} returned payload: {payload}'


def create_lambda_tool_from_discovery(
    function_name: str,
    tool_def: Dict[str, Any]
) -> None:
    """
    Create an MCP tool from a discovered tool definition.
    
    Args:
        function_name: Name of the Lambda function
        tool_def: Tool definition from discovery response
    """
    tool_name = tool_def.get('name')
    if not tool_name:
        logger.warning(f'Tool definition missing name in function {function_name}')
        return
    
    # Sanitize tool name
    sanitized_name = sanitize_tool_name(tool_name)
    
    description = tool_def.get('description', f'Tool {tool_name} from Lambda function {function_name}')
    input_schema = tool_def.get('inputSchema', {})
    
    # Create the tool handler function
    async def tool_handler(parameters: dict) -> str:
        """Dynamically created tool handler."""
        return await invoke_lambda_tool_impl(function_name, tool_name, parameters)
    
    # Set the function's documentation
    tool_handler.__doc__ = description
    
    # Use the tool name directly from the Lambda function
    full_tool_name = sanitized_name
    
    logger.info(f'Registering tool {full_tool_name} from function {function_name}')
    
    # Register the tool with ChukMCPServer
    # The tool decorator will handle the schema from the function signature
    # We'll pass the input schema as part of the description for now
    if input_schema:
        full_description = f'{description}\n\nInput Schema:\n{json.dumps(input_schema, indent=2)}'
    else:
        full_description = description
    
    tool_handler.__doc__ = full_description
    
    # Apply the decorator manually
    decorated_function = mcp.tool(name=full_tool_name)(tool_handler)


def create_legacy_lambda_tool(function_name: str, description: str, schema_arn: Optional[str] = None):
    """
    Create a legacy tool function for a Lambda function that doesn't support discovery.
    
    Args:
        function_name: Name of the Lambda function
        description: Base description for the tool
        schema_arn: Optional ARN of the input schema in the Schema Registry
    """
    # Create a meaningful tool name
    tool_name = sanitize_tool_name(function_name)

    # Build the full description with schema if available
    full_description = description
    if schema_arn:
        schema = get_schema_from_registry(schema_arn)
        if schema:
            full_description = f'{description}\n\nInput Schema:\n{schema}'
            logger.info(f'Added schema from registry to description for function {function_name}')

    # Define the inner function with proper docstring
    async def lambda_function(parameters: dict) -> str:
        """Tool for invoking a specific AWS Lambda function with parameters."""
        return await invoke_lambda_function_impl(function_name, parameters)

    # Set the function's documentation
    lambda_function.__doc__ = full_description

    logger.info(f'Registering legacy tool {tool_name} with description: {description}')
    # Apply the decorator manually with the specific name
    decorated_function = mcp.tool(name=tool_name)(lambda_function)

    return decorated_function


def get_schema_from_registry(schema_arn: str) -> Optional[dict]:
    """Fetch schema from EventBridge Schema Registry.

    Args:
        schema_arn: ARN of the schema to fetch

    Returns:
        Schema content if successful, None if failed
    """
    try:
        # Parse registry name and schema name from ARN
        # ARN format: arn:aws:schemas:region:account:schema/registry-name/schema-name
        arn_parts = schema_arn.split(':')
        if len(arn_parts) < 6:
            logger.error(f'Invalid schema ARN format: {schema_arn}')
            return None

        registry_schema = arn_parts[5].split('/')
        if len(registry_schema) != 3:
            logger.error(f'Invalid schema path in ARN: {arn_parts[5]}')
            return None

        registry_name = registry_schema[1]
        schema_name = registry_schema[2]

        # Get the latest schema version
        response = schemas_client.describe_schema(
            RegistryName=registry_name,
            SchemaName=schema_name,
        )

        # Return the raw schema content
        return response['Content']

    except Exception as e:
        logger.error(f'Error fetching schema from registry: {e}')
        return None


def get_schema_arn_from_function_arn(function_arn: str) -> Optional[str]:
    """Get schema ARN from function tags if configured.

    Args:
        function_arn: ARN of the Lambda function

    Returns:
        Schema ARN if found and configured, None otherwise
    """
    if not FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY:
        logger.info(
            'No schema tag environment variable provided (FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY ).'
        )
        return None

    try:
        tags_response = lambda_client.list_tags(Resource=function_arn)
        tags = tags_response.get('Tags', {})
        if FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY in tags:
            return tags[FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY]
        else:
            logger.info(
                f'No schema arn provided for function {function_arn} via tag {FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY}'
            )
    except Exception as e:
        logger.warning(f'Error checking tags for function {function_arn}: {e}')

    return None


def filter_functions_by_tag(functions, tag_key, tag_value):
    """Filter Lambda functions by a specific tag key-value pair.

    Args:
        functions: List of Lambda function objects
        tag_key: Tag key to filter by
        tag_value: Tag value to filter by

    Returns:
        List of Lambda functions that have the specified tag key-value pair
    """
    logger.info(f'Filtering functions by tag key-value pair: {tag_key}={tag_value}')
    tagged_functions = []

    for function in functions:
        try:
            # Get tags for the function
            tags_response = lambda_client.list_tags(Resource=function['FunctionArn'])
            tags = tags_response.get('Tags', {})

            # Check if the function has the specified tag key-value pair
            if tag_key in tags and tags[tag_key] == tag_value:
                tagged_functions.append(function)
        except Exception as e:
            logger.warning(f'Error getting tags for function {function["FunctionName"]}: {e}')

    logger.info(f'{len(tagged_functions)} Lambda functions found with tag {tag_key}={tag_value}.')
    return tagged_functions


def get_all_lambda_functions():
    """Retrieve all available Lambda functions using pagination."""
    paginator = lambda_client.get_paginator('list_functions')
    all_functions = []

    for page in paginator.paginate():
        all_functions.extend(page.get('Functions', []))

    return all_functions


def register_lambda_functions():
    """Register Lambda functions as individual tools with tool discovery support."""
    try:
        logger.info('Registering Lambda functions with tool discovery...')

        # Get all functions
        all_functions = get_all_lambda_functions()
        logger.info(f'Total Lambda functions found: {len(all_functions)}')

        # First filter by function name if prefix or list is set
        if FUNCTION_PREFIX or FUNCTION_LIST:
            valid_functions = [
                f for f in all_functions if validate_function_name(f['FunctionName'])
            ]
            logger.info(f'{len(valid_functions)} Lambda functions found after name filtering.')
        else:
            valid_functions = all_functions
            logger.info(
                'No name filtering applied (both FUNCTION_PREFIX and FUNCTION_LIST are empty).'
            )

        # Then filter by tag if both FUNCTION_TAG_KEY and FUNCTION_TAG_VALUE are set and non-empty
        if FUNCTION_TAG_KEY and FUNCTION_TAG_VALUE:
            tagged_functions = filter_functions_by_tag(
                valid_functions, FUNCTION_TAG_KEY, FUNCTION_TAG_VALUE
            )
            valid_functions = tagged_functions
        elif FUNCTION_TAG_KEY or FUNCTION_TAG_VALUE:
            logger.warning(
                'Both FUNCTION_TAG_KEY and FUNCTION_TAG_VALUE must be set to filter by tag.'
            )
            valid_functions = []

        # Register tools for each function
        for function in valid_functions:
            function_name = function['FunctionName']
            description = function.get('Description', f'AWS Lambda function: {function_name}')
            
            # Try to discover tools from the function
            tools = discover_tools_from_lambda(function_name)
            
            if tools:
                # Register each discovered tool
                logger.info(f'Registering {len(tools)} tools from function {function_name}')
                for tool_def in tools:
                    create_lambda_tool_from_discovery(function_name, tool_def)
            else:
                # Fall back to legacy mode - single tool per function
                logger.info(f'Using legacy mode for function {function_name}')
                schema_arn = get_schema_arn_from_function_arn(function['FunctionArn'])
                create_legacy_lambda_tool(function_name, description, schema_arn)

        logger.info('Lambda functions registered successfully.')

    except Exception as e:
        logger.error(f'Error registering Lambda functions as tools: {e}')


def main():
    """Run the MCP server with CLI argument support."""
    register_lambda_functions()

    mcp.run()


if __name__ == '__main__':
    main()
