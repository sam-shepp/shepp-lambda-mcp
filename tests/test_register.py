"""Tests for function discovery, tag filtering, and registration orchestration."""

import logging
import pytest
from unittest.mock import MagicMock, patch


with pytest.MonkeyPatch().context() as CTX:
    CTX.setattr('boto3.Session', MagicMock)
    from awslabs.lambda_tool_mcp_server.server import (
        filter_functions_by_tag,
        get_all_lambda_functions,
        register_lambda_functions,
    )


class TestGetAllLambdaFunctions:
    """Tests for get_all_lambda_functions pagination."""

    def test_aggregates_all_pages(self):
        """Functions from every page are concatenated."""
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {'Functions': [{'FunctionName': 'a'}]},
            {'Functions': [{'FunctionName': 'b'}, {'FunctionName': 'c'}]},
        ]
        client.get_paginator.return_value = paginator

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', client):
            result = get_all_lambda_functions()

        assert [f['FunctionName'] for f in result] == ['a', 'b', 'c']


class TestFilterFunctionsByTag:
    """Tests for filter_functions_by_tag."""

    def test_matching_tags(self, mock_lambda_client, sample_functions):
        """Only functions carrying the exact tag key/value are returned."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = filter_functions_by_tag(sample_functions, 'test-key', 'test-value')

        names = [f['FunctionName'] for f in result]
        assert names == ['test-function-1', 'prefix-test-function-3']

    def test_no_matching_tags(self, mock_lambda_client, sample_functions):
        """No matches yields an empty list."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            result = filter_functions_by_tag(sample_functions, 'nope', 'nope')

        assert result == []

    def test_error_getting_tags_is_swallowed(self, mock_lambda_client, sample_functions, caplog):
        """A list_tags error is logged and the function is skipped, not raised."""
        mock_lambda_client.list_tags.side_effect = Exception('Access denied')

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            with caplog.at_level(logging.WARNING):
                result = filter_functions_by_tag(sample_functions, 'test-key', 'test-value')

        assert result == []
        assert 'Error getting tags for function' in caplog.text


class TestRegisterLambdaFunctions:
    """Tests for register_lambda_functions orchestration.

    Discovery is forced to return None so registration takes the legacy path, which
    makes one create_legacy_lambda_tool call per selected function.
    """

    @patch('awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda', return_value=None)
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_no_filters_registers_all(self, mock_legacy, _mock_disco, mock_lambda_client):
        """With no filters every function is registered."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            register_lambda_functions()

        assert mock_legacy.call_count == 4
        mock_legacy.assert_any_call('test-function-1', 'Test function 1 description', None)
        mock_legacy.assert_any_call('other-function', '', None)

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_PREFIX', 'prefix-')
    @patch('awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda', return_value=None)
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_prefix_filter(self, mock_legacy, _mock_disco, mock_lambda_client):
        """Only functions matching the prefix are registered."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            register_lambda_functions()

        assert mock_legacy.call_count == 1
        mock_legacy.assert_called_with(
            'prefix-test-function-3', 'Test function 3 with prefix', None
        )

    @patch(
        'awslabs.lambda_tool_mcp_server.server.FUNCTION_LIST',
        ['test-function-1', 'test-function-2'],
    )
    @patch('awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda', return_value=None)
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_list_filter(self, mock_legacy, _mock_disco, mock_lambda_client):
        """Only functions in the list are registered."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            register_lambda_functions()

        assert mock_legacy.call_count == 2
        mock_legacy.assert_any_call('test-function-1', 'Test function 1 description', None)
        mock_legacy.assert_any_call('test-function-2', 'Test function 2 description', None)

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_TAG_KEY', 'test-key')
    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_TAG_VALUE', 'test-value')
    @patch('awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda', return_value=None)
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_tag_filter(self, mock_legacy, _mock_disco, mock_lambda_client):
        """Only functions carrying the matching tag are registered."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            register_lambda_functions()

        assert mock_legacy.call_count == 2
        mock_legacy.assert_any_call('test-function-1', 'Test function 1 description', None)
        mock_legacy.assert_any_call('prefix-test-function-3', 'Test function 3 with prefix', None)

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_TAG_KEY', 'test-key')
    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_TAG_VALUE', '')
    @patch('awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda', return_value=None)
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_incomplete_tag_config_registers_nothing(
        self, mock_legacy, _mock_disco, mock_lambda_client, caplog
    ):
        """Setting only one of tag key/value registers nothing and warns."""
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            with caplog.at_level(logging.WARNING):
                register_lambda_functions()

        assert mock_legacy.call_count == 0
        assert (
            'Both FUNCTION_TAG_KEY and FUNCTION_TAG_VALUE must be set to filter by tag'
            in caplog.text
        )

    @patch('awslabs.lambda_tool_mcp_server.server.create_lambda_tool_from_discovery')
    @patch('awslabs.lambda_tool_mcp_server.server.create_legacy_lambda_tool')
    def test_discovery_path_registers_each_discovered_tool(
        self, mock_legacy, mock_from_disco, mock_lambda_client
    ):
        """When discovery returns tools, each tool is registered and legacy is skipped."""
        tools = [{'name': 'add'}, {'name': 'sub'}]
        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            with patch(
                'awslabs.lambda_tool_mcp_server.server.discover_tools_from_lambda',
                return_value=tools,
            ):
                register_lambda_functions()

        mock_legacy.assert_not_called()
        # 4 functions x 2 discovered tools each.
        assert mock_from_disco.call_count == 8

    def test_error_handling_does_not_raise(self, mock_lambda_client):
        """A failure while listing functions is caught and logged, not raised."""
        mock_lambda_client.get_paginator.side_effect = Exception('Error listing functions')

        with patch('awslabs.lambda_tool_mcp_server.server.lambda_client', mock_lambda_client):
            register_lambda_functions()  # should not raise
