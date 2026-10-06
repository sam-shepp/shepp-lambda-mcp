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
    """Tests for plain successful Lambda payload formatting."""

    def test_json_object_is_compact_and_unlabelled(self):
        payload = json.dumps({'result': 'success'}).encode()
        result = format_lambda_response('internal-function', 'my-tool', payload)
        assert result == '{"result":"success"}'
        assert 'internal-function' not in result
        assert 'my-tool' not in result

    @pytest.mark.parametrize(
        ('value', 'expected'),
        [
            ([1, 2, 3], '[1,2,3]'),
            ('hello', '"hello"'),
            (42, '42'),
            (True, 'true'),
            (None, 'null'),
        ],
    )
    def test_json_values_are_compact(self, value, expected):
        payload = json.dumps(value).encode()
        assert format_lambda_response('function', 'tool', payload) == expected

    def test_unicode_is_not_ascii_escaped(self):
        payload = json.dumps({'city': 'Montréal'}).encode()
        assert format_lambda_response('function', 'tool', payload) == '{"city":"Montréal"}'

    def test_non_json_utf8_is_undecorated(self):
        payload = b'Non-JSON response'
        assert format_lambda_response('function', 'tool', payload) == 'Non-JSON response'

    def test_malformed_json_is_plain_text(self):
        payload = b'{invalid json}'
        assert format_lambda_response('function', 'tool', payload) == '{invalid json}'

    def test_invalid_utf8_has_safe_undecorated_representation(self):
        payload = bytes([0x80, 0x81, 0x82, 0x83])
        result = format_lambda_response('function', 'tool', payload)
        assert result == repr(payload)
        assert 'function' not in result
        assert 'tool' not in result


class TestMain:
    """Tests for the main entrypoint."""

    @patch('awslabs.lambda_tool_mcp_server.server.register_lambda_functions')
    @patch('awslabs.lambda_tool_mcp_server.server.mcp')
    def test_main_registers_and_runs(self, mock_mcp, mock_register):
        """Main registers functions then starts the server."""
        main()

        mock_register.assert_called_once_with()
        mock_mcp.run.assert_called_once_with()
