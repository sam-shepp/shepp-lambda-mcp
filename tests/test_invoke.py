"""Tests for the Lambda invocation implementations (tool and legacy)."""

import json
import pytest
from unittest.mock import MagicMock, patch


with pytest.MonkeyPatch().context() as CTX:
    CTX.setattr('boto3.Session', MagicMock)
    from awslabs.lambda_tool_mcp_server.server import (
        invoke_lambda_function_impl,
        invoke_lambda_tool_impl,
    )


class TestInvokeLambdaToolImpl:
    """Tests for invoke_lambda_tool_impl (the tool-discovery invocation path)."""

    @pytest.mark.asyncio
    async def test_successful_invocation_wraps_tool_envelope(self, mock_lambda_client):
        """A successful invoke sends the tool/arguments envelope and formats the reply."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_tool_impl(
                'test-function-1', 'my-tool', {'param': 'value'}
            )

        mock_lambda_client.invoke.assert_called_once_with(
            FunctionName='test-function-1',
            InvocationType='RequestResponse',
            Payload=json.dumps({'tool': 'my-tool', 'arguments': {'param': 'value'}}),
        )
        assert 'Tool my-tool (function test-function-1) returned:' in result
        assert '"result": "success"' in result

    @pytest.mark.asyncio
    async def test_function_error(self, mock_lambda_client):
        """A FunctionError in the response is surfaced as an error string."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_tool_impl('error-function', 'my-tool', {})

        assert 'Tool my-tool in function error-function returned with error:' in result

    @pytest.mark.asyncio
    async def test_non_json_response(self, mock_lambda_client):
        """A non-JSON payload is returned raw."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_tool_impl('test-function-2', 'my-tool', {})

        assert 'returned payload:' in result
        assert 'Non-JSON response' in result

    @pytest.mark.asyncio
    async def test_string_parameters_are_parsed(self, mock_lambda_client):
        """Parameters passed as a JSON string are parsed into a dict before invoking."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            await invoke_lambda_tool_impl('test-function-1', 'my-tool', '{"param": "value"}')

        _, kwargs = mock_lambda_client.invoke.call_args
        assert json.loads(kwargs['Payload']) == {
            'tool': 'my-tool',
            'arguments': {'param': 'value'},
        }

    @pytest.mark.asyncio
    async def test_empty_string_parameters_become_empty_dict(self, mock_lambda_client):
        """An empty string parameter is treated as no arguments."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            await invoke_lambda_tool_impl('test-function-1', 'my-tool', '')

        _, kwargs = mock_lambda_client.invoke.call_args
        assert json.loads(kwargs['Payload'])['arguments'] == {}

    @pytest.mark.asyncio
    async def test_invalid_string_parameters_fall_back_to_empty_dict(
        self, mock_lambda_client, caplog
    ):
        """A non-JSON string parameter logs a warning and falls back to an empty dict."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            await invoke_lambda_tool_impl('test-function-1', 'my-tool', 'not json')

        _, kwargs = mock_lambda_client.invoke.call_args
        assert json.loads(kwargs['Payload'])['arguments'] == {}


class TestInvokeLambdaFunctionImpl:
    """Tests for invoke_lambda_function_impl (the legacy, whole-payload path)."""

    @pytest.mark.asyncio
    async def test_successful_invocation_sends_raw_parameters(self, mock_lambda_client):
        """Legacy invoke passes the parameters straight through as the payload."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_function_impl('test-function-1', {'param': 'value'})

        mock_lambda_client.invoke.assert_called_once_with(
            FunctionName='test-function-1',
            InvocationType='RequestResponse',
            Payload=json.dumps({'param': 'value'}),
        )
        assert 'Function test-function-1 returned:' in result
        assert '"result": "success"' in result

    @pytest.mark.asyncio
    async def test_function_error(self, mock_lambda_client):
        """A FunctionError is surfaced as an error string."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_function_impl('error-function', {'param': 'value'})

        assert 'Function error-function returned with error:' in result

    @pytest.mark.asyncio
    async def test_non_json_response(self, mock_lambda_client):
        """A non-JSON payload is returned raw."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = await invoke_lambda_function_impl('test-function-2', {'param': 'value'})

        assert "Function test-function-2 returned payload: b'Non-JSON response'" == result
