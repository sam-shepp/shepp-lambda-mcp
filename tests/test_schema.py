"""Tests for EventBridge Schema Registry integration."""

import logging
import pytest
from unittest.mock import MagicMock, patch


with pytest.MonkeyPatch().context() as CTX:
    CTX.setattr('boto3.Session', MagicMock)
    from awslabs.lambda_tool_mcp_server.server import (
        get_schema_arn_from_function_arn,
        get_schema_from_registry,
    )


VALID_ARN = 'arn:aws:schemas:us-east-1:123456789012:schema/registry-name/schema-name'


class TestGetSchemaFromRegistry:
    """Tests for get_schema_from_registry."""

    def test_valid_arn_returns_content(self):
        """A valid ARN fetches the schema and returns its content."""
        content = {'type': 'object', 'properties': {'test': {'type': 'string'}}}
        with patch('awslabs.lambda_tool_mcp_server.server.schemas_client') as mock_client:
            mock_client.describe_schema.return_value = {'Content': content}

            result = get_schema_from_registry(VALID_ARN)

        assert result == content
        mock_client.describe_schema.assert_called_once_with(
            RegistryName='registry-name',
            SchemaName='schema-name',
        )

    def test_invalid_arn_format(self, caplog):
        """An ARN with too few segments is rejected without calling the client."""
        with patch('awslabs.lambda_tool_mcp_server.server.schemas_client') as mock_client:
            with caplog.at_level(logging.ERROR):
                result = get_schema_from_registry('invalid:arn:format')

        assert result is None
        assert 'Invalid schema ARN format' in caplog.text
        mock_client.describe_schema.assert_not_called()

    def test_invalid_schema_path(self, caplog):
        """An ARN whose schema path is not registry/schema is rejected."""
        with patch('awslabs.lambda_tool_mcp_server.server.schemas_client') as mock_client:
            with caplog.at_level(logging.ERROR):
                result = get_schema_from_registry(
                    'arn:aws:schemas:us-east-1:123456789012:schema/invalid-path'
                )

        assert result is None
        assert 'Invalid schema path in ARN' in caplog.text
        mock_client.describe_schema.assert_not_called()

    def test_client_error(self, caplog):
        """A client exception is logged and yields None."""
        with patch('awslabs.lambda_tool_mcp_server.server.schemas_client') as mock_client:
            mock_client.describe_schema.side_effect = Exception('Schema client error')

            with caplog.at_level(logging.ERROR):
                result = get_schema_from_registry(VALID_ARN)

        assert result is None
        assert 'Error fetching schema from registry' in caplog.text


class TestGetSchemaArnFromFunctionArn:
    """Tests for get_schema_arn_from_function_arn."""

    def test_returns_arn_from_tag(self):
        """The schema ARN tag value is returned when present."""
        schema_arn = 'arn:aws:schemas:us-east-1:123456789012:schema/registry/schema'
        with patch(
            'awslabs.lambda_tool_mcp_server.server.FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY',
            'schema-arn-tag',
        ):
            with patch('awslabs.lambda_tool_mcp_server.server.lambda_client') as mock_client:
                mock_client.list_tags.return_value = {'Tags': {'schema-arn-tag': schema_arn}}

                result = get_schema_arn_from_function_arn('test-function-arn')

        assert result == schema_arn

    def test_no_tag_key_configured_skips_lookup(self):
        """When the tag key env var is unset, no tag lookup happens."""
        with patch(
            'awslabs.lambda_tool_mcp_server.server.FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY', None
        ):
            with patch('awslabs.lambda_tool_mcp_server.server.lambda_client') as mock_client:
                result = get_schema_arn_from_function_arn('test-function-arn')

        assert result is None
        mock_client.list_tags.assert_not_called()

    def test_tag_not_found_returns_none(self):
        """When the configured tag is absent, None is returned."""
        with patch(
            'awslabs.lambda_tool_mcp_server.server.FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY',
            'schema-arn-tag',
        ):
            with patch('awslabs.lambda_tool_mcp_server.server.lambda_client') as mock_client:
                mock_client.list_tags.return_value = {'Tags': {'different-tag': 'value'}}

                result = get_schema_arn_from_function_arn('test-function-arn')

        assert result is None

    def test_client_error_returns_none(self, caplog):
        """A list_tags error is logged and yields None."""
        with patch(
            'awslabs.lambda_tool_mcp_server.server.FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY',
            'schema-arn-tag',
        ):
            with patch('awslabs.lambda_tool_mcp_server.server.lambda_client') as mock_client:
                mock_client.list_tags.side_effect = Exception('Tag retrieval error')

                with caplog.at_level(logging.WARNING):
                    result = get_schema_arn_from_function_arn('test-function-arn')

        assert result is None
        assert 'Error checking tags for function' in caplog.text
