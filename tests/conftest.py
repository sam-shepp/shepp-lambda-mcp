"""Test fixtures for the shepp-lambda-mcp tests.

The server module builds its boto3 clients at import time, so every test module
imports it under a mocked ``boto3.Session`` (see the guarded imports at the top of
each test file). These fixtures provide a mock Lambda client whose behaviour matches
the ChukMCPServer-based server: it lists functions, returns tags, and answers both
the tool-discovery probe and normal tool/legacy invokes.
"""

import json
import pytest
from unittest.mock import MagicMock


# A discovery payload the server sends to probe a function for tool support.
DISCOVERY_ACTION = 'discover_tools'


@pytest.fixture
def sample_functions():
    """Return the list of Lambda function objects used across the tests."""
    return [
        {
            'FunctionName': 'test-function-1',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function-1',
            'Description': 'Test function 1 description',
        },
        {
            'FunctionName': 'test-function-2',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function-2',
            'Description': 'Test function 2 description',
        },
        {
            'FunctionName': 'prefix-test-function-3',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:prefix-test-function-3',
            'Description': 'Test function 3 with prefix',
        },
        {
            'FunctionName': 'other-function',
            'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:other-function',
            'Description': '',  # Empty description
        },
    ]


def _payload(data):
    """Wrap ``data`` in an object whose ``.read()`` returns encoded bytes."""
    mock_payload = MagicMock()
    if isinstance(data, (bytes, bytearray)):
        mock_payload.read.return_value = bytes(data)
    else:
        mock_payload.read.return_value = json.dumps(data).encode()
    return mock_payload


@pytest.fixture
def mock_lambda_client(sample_functions):
    """Create a mock boto3 Lambda client.

    Discovery probes return a payload *without* a ``tools`` array, so functions fall
    back to legacy single-tool registration by default. Individual tests that need the
    discovery path patch ``discover_tools_from_lambda`` directly.
    """
    mock_client = MagicMock()

    paginator_mock = MagicMock()
    paginator_mock.paginate.return_value = [{'Functions': sample_functions}]
    mock_client.get_paginator.return_value = paginator_mock

    def mock_list_tags(Resource):
        if 'test-function-1' in Resource:
            return {'Tags': {'test-key': 'test-value'}}
        elif 'test-function-2' in Resource:
            return {'Tags': {'other-key': 'other-value'}}
        elif 'prefix-test-function-3' in Resource:
            return {'Tags': {'test-key': 'test-value'}}
        else:
            return {'Tags': {}}

    mock_client.list_tags.side_effect = mock_list_tags

    def mock_invoke(FunctionName, InvocationType, Payload):
        parsed = json.loads(Payload)

        # Discovery probe: no function here advertises tools, forcing legacy mode.
        if isinstance(parsed, dict) and parsed.get('action') == DISCOVERY_ACTION:
            return {'StatusCode': 200, 'Payload': _payload({})}

        if FunctionName == 'test-function-1':
            return {'StatusCode': 200, 'Payload': _payload({'result': 'success'})}
        elif FunctionName == 'test-function-2':
            return {'StatusCode': 200, 'Payload': _payload(b'Non-JSON response')}
        elif FunctionName == 'error-function':
            return {
                'StatusCode': 200,
                'FunctionError': 'Handled',
                'Payload': _payload({'error': 'Function error'}),
            }
        else:
            return {'StatusCode': 200, 'Payload': _payload({})}

    mock_client.invoke.side_effect = mock_invoke

    return mock_client


@pytest.fixture
def server_module():
    """Import the server module (under a mocked Session) and clear its MCP tools.

    Tools are cleared before and after the test so real registrations made against the
    shared ``mcp`` instance don't leak between tests.
    """
    with pytest.MonkeyPatch().context() as ctx:
        ctx.setattr('boto3.Session', MagicMock)
        import awslabs.lambda_tool_mcp_server.server as server

    server.mcp.clear_tools()
    yield server
    server.mcp.clear_tools()
