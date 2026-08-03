"""Tests for tool discovery and dynamic tool creation."""

import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


with pytest.MonkeyPatch().context() as CTX:
    CTX.setattr('boto3.Session', MagicMock)
    from awslabs.lambda_tool_mcp_server.server import (
        create_lambda_tool_from_discovery,
        create_legacy_lambda_tool,
        discover_tools_from_lambda,
    )


def _client_returning(payload_obj, function_error=None):
    """Build a mock lambda client whose invoke returns the given payload."""
    client = MagicMock()
    read_mock = MagicMock()
    read_mock.read.return_value = json.dumps(payload_obj).encode()
    response = {'StatusCode': 200, 'Payload': read_mock}
    if function_error:
        response['FunctionError'] = function_error
    client.invoke.return_value = response
    return client


def _tool_by_name(server_module, name):
    """Return the registered ToolHandler with the given name, or None."""
    for tool in server_module.mcp.get_tools():
        if tool.name == name:
            return tool
    return None


class TestDiscoverToolsFromLambda:
    """Tests for discover_tools_from_lambda."""

    def test_returns_tools_when_present(self):
        """A discovery response with a tools array returns that array."""
        tools = [{'name': 'add', 'description': 'Add numbers'}]
        client = _client_returning({'tools': tools})

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', client):
            result = discover_tools_from_lambda('disco-function')

        assert result == tools
        _, kwargs = client.invoke.call_args
        assert json.loads(kwargs['Payload']) == {'action': 'discover_tools'}

    def test_function_error_returns_none(self):
        """A FunctionError during discovery yields None (falls back to legacy)."""
        client = _client_returning({'tools': []}, function_error='Unhandled')

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', client):
            result = discover_tools_from_lambda('disco-function')

        assert result is None

    def test_missing_tools_key_returns_none(self):
        """A response without a tools key is not a discovery response."""
        client = _client_returning({'result': 'ok'})

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', client):
            result = discover_tools_from_lambda('disco-function')

        assert result is None

    def test_exception_returns_none(self):
        """An exception during invoke is swallowed and yields None."""
        client = MagicMock()
        client.invoke.side_effect = Exception('boom')

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', client):
            result = discover_tools_from_lambda('disco-function')

        assert result is None


class TestCreateLambdaToolFromDiscovery:
    """Tests for create_lambda_tool_from_discovery."""

    def test_registers_tool_with_sanitized_name(self, server_module):
        """A discovered tool is registered under its sanitized name."""
        create_lambda_tool_from_discovery(
            'my-function', {'name': 'do-thing', 'description': 'Does a thing'}
        )

        tool = _tool_by_name(server_module, 'do_thing')
        assert tool is not None
        assert 'Does a thing' in tool.description

    def test_missing_name_skips_registration(self, server_module, caplog):
        """A tool definition without a name is skipped with a warning."""
        before = len(server_module.mcp.get_tools())
        with caplog.at_level(logging.WARNING):
            create_lambda_tool_from_discovery('my-function', {'description': 'no name'})

        assert len(server_module.mcp.get_tools()) == before
        assert 'missing name' in caplog.text

    def test_input_schema_added_to_description(self, server_module):
        """An inputSchema is embedded in the registered tool's description."""
        schema = {'type': 'object', 'properties': {'x': {'type': 'number'}}}
        create_lambda_tool_from_discovery(
            'my-function',
            {'name': 'calc', 'description': 'Calculate', 'inputSchema': schema},
        )

        tool = _tool_by_name(server_module, 'calc')
        assert 'Input Schema:' in tool.description
        assert '"type": "number"' in tool.description

    @pytest.mark.asyncio
    async def test_handler_delegates_to_tool_impl(self, server_module):
        """Invoking the registered handler delegates to invoke_lambda_tool_impl."""
        create_lambda_tool_from_discovery(
            'my-function', {'name': 'do-thing', 'description': 'Does a thing'}
        )
        tool = _tool_by_name(server_module, 'do_thing')

        with patch.object(
            server_module, 'invoke_lambda_tool_impl', new=AsyncMock(return_value='delegated')
        ) as mock_impl:
            result = await tool.handler({'a': 1})

        assert result == 'delegated'
        mock_impl.assert_awaited_once_with('my-function', 'do-thing', {'a': 1})


class TestCreateLegacyLambdaTool:
    """Tests for create_legacy_lambda_tool."""

    def test_registers_with_sanitized_name_and_description(self, server_module):
        """A legacy tool is registered under the sanitized function name."""
        create_legacy_lambda_tool('my-function', 'A description')

        tool = _tool_by_name(server_module, 'my_function')
        assert tool is not None
        assert tool.description == 'A description'

    def test_schema_arn_appends_schema_to_description(self, server_module):
        """When a schema ARN resolves, the schema is appended to the description."""
        schema = {'type': 'object'}
        with patch.object(
            server_module, 'get_schema_from_registry', return_value=schema
        ) as mock_get:
            create_legacy_lambda_tool('my-function', 'Base desc', schema_arn='arn:schema')

        mock_get.assert_called_once_with('arn:schema')
        tool = _tool_by_name(server_module, 'my_function')
        assert 'Base desc' in tool.description
        assert 'Input Schema:' in tool.description

    def test_schema_fetch_failure_keeps_base_description(self, server_module):
        """If schema resolution fails, the base description is used unchanged."""
        with patch.object(server_module, 'get_schema_from_registry', return_value=None):
            create_legacy_lambda_tool('my-function', 'Base desc', schema_arn='arn:schema')

        tool = _tool_by_name(server_module, 'my_function')
        assert tool.description == 'Base desc'

    @pytest.mark.asyncio
    async def test_handler_delegates_to_function_impl(self, server_module):
        """Invoking the registered legacy handler delegates to invoke_lambda_function_impl."""
        create_legacy_lambda_tool('my-function', 'A description')
        tool = _tool_by_name(server_module, 'my_function')

        with patch.object(
            server_module,
            'invoke_lambda_function_impl',
            new=AsyncMock(return_value='delegated'),
        ) as mock_impl:
            result = await tool.handler({'a': 1})

        assert result == 'delegated'
        mock_impl.assert_awaited_once_with('my-function', {'a': 1})
