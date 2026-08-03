"""Tests for the pure helper functions and entrypoint of the server module."""

import json
import pytest
from unittest.mock import MagicMock, patch


with pytest.MonkeyPatch().context() as CTX:
    CTX.setattr('boto3.Session', MagicMock)
    from awslabs.lambda_tool_mcp_server.server import (
        format_lambda_response,
        main,
        sanitize_tool_name,
        validate_function_name,
    )


class TestValidateFunctionName:
    """Tests for the validate_function_name function."""

    def test_empty_prefix_and_list(self):
        """With no prefix and no list, every function is valid."""
        assert validate_function_name('any-function') is True

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_PREFIX', 'test-')
    def test_prefix_match(self):
        """A function matching the prefix is valid; others are not."""
        assert validate_function_name('test-function') is True
        assert validate_function_name('other-function') is False

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_LIST', ['func1', 'func2', 'func3'])
    def test_list_match(self):
        """A function present in the list is valid; others are not."""
        assert validate_function_name('func1') is True
        assert validate_function_name('func2') is True
        assert validate_function_name('other-func') is False

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_PREFIX', 'test-')
    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_LIST', ['func1', 'func2'])
    def test_prefix_and_list(self):
        """Either a prefix match or a list membership makes a function valid."""
        assert validate_function_name('test-function') is True
        assert validate_function_name('func1') is True
        assert validate_function_name('other-func') is False

    @patch('awslabs.lambda_tool_mcp_server.server.FUNCTION_PREFIX', 'test-')
    def test_empty_name_with_prefix(self):
        """An empty name never matches a non-empty prefix."""
        assert validate_function_name('') is False


class TestSanitizeToolName:
    """Tests for the sanitize_tool_name function."""

    def test_invalid_characters(self):
        """Invalid characters are replaced with underscores."""
        assert (
            sanitize_tool_name('function-name.with:invalid@chars')
            == 'function_name_with_invalid_chars'
        )

    def test_numeric_first_character(self):
        """A leading digit is prefixed with an underscore."""
        assert sanitize_tool_name('123function') == '_123function'

    def test_valid_name(self):
        """An already-valid name is returned unchanged."""
        assert sanitize_tool_name('valid_function_name') == 'valid_function_name'

    def test_empty_name(self):
        """An empty name stays empty."""
        assert sanitize_tool_name('') == ''

    def test_only_invalid_characters(self):
        """A name of only invalid characters becomes all underscores."""
        assert sanitize_tool_name('!@#$%^') == '______'


class TestFormatLambdaResponse:
    """Tests for the format_lambda_response function (tool-aware, 3-arg)."""

    def test_json_payload(self):
        """A JSON payload is pretty-printed and labelled with tool and function."""
        payload = json.dumps({'result': 'success'}).encode()
        result = format_lambda_response('test-function', 'my-tool', payload)
        assert 'Tool my-tool (function test-function) returned:' in result
        assert '"result": "success"' in result

    def test_non_json_payload(self):
        """A non-JSON payload is returned raw."""
        payload = b'Non-JSON response'
        result = format_lambda_response('test-function', 'my-tool', payload)
        assert (
            "Tool my-tool (function test-function) returned payload: b'Non-JSON response'"
            == result
        )

    def test_invalid_json_payload(self):
        """A malformed JSON payload falls back to the raw representation."""
        payload = b'{invalid json}'
        result = format_lambda_response('test-function', 'my-tool', payload)
        assert 'Tool my-tool (function test-function) returned payload:' in result

    def test_unicode_decode_error(self):
        """A payload that is invalid UTF-8 is handled without raising."""
        payload = b'\x80\x81\x82\x83'
        result = format_lambda_response('test-function', 'my-tool', payload)
        assert 'Tool my-tool (function test-function) returned payload:' in result
        assert str(payload) in result


class TestMain:
    """Tests for the main entrypoint."""

    @patch('awslabs.lambda_tool_mcp_server.server.register_lambda_functions')
    @patch('awslabs.lambda_tool_mcp_server.server.mcp')
    def test_main_registers_and_runs(self, mock_mcp, mock_register):
        """Main registers functions then starts the server."""
        main()

        mock_register.assert_called_once_with()
        mock_mcp.run.assert_called_once_with()
