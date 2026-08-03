"""Tests for the boto3 client configuration (read timeout) of the lambda-tool-mcp-server."""

import importlib
import pytest
from unittest.mock import MagicMock


def _reload_server_with_mock_session(monkeypatch):
    """Reload the server module with boto3.Session mocked out.

    Returns the reloaded server module and the mock Session instance so tests can
    inspect the arguments the module used to build its boto3 clients at import time.
    """
    mock_session_instance = MagicMock()
    mock_session_cls = MagicMock(return_value=mock_session_instance)
    monkeypatch.setattr('boto3.Session', mock_session_cls)

    import awslabs.lambda_tool_mcp_server.server as server

    server = importlib.reload(server)
    return server, mock_session_instance


def _client_kwargs_for(mock_session_instance, service_name):
    """Return the kwargs passed to session.client(service_name, ...)."""
    for call in mock_session_instance.client.call_args_list:
        args, kwargs = call
        if args and args[0] == service_name:
            return kwargs
    raise AssertionError(f'session.client was never called for {service_name!r}')


class TestLambdaClientReadTimeout:
    """Tests for the read-timeout Config applied to the boto3 clients."""

    def test_default_read_timeout(self, monkeypatch):
        """The lambda client defaults to a 300s read timeout when the env var is unset."""
        monkeypatch.delenv('LAMBDA_INVOKE_READ_TIMEOUT', raising=False)
        server, mock_session = _reload_server_with_mock_session(monkeypatch)

        assert server.LAMBDA_INVOKE_READ_TIMEOUT == 300

        config = _client_kwargs_for(mock_session, 'lambda')['config']
        assert config.read_timeout == 300
        assert config.connect_timeout == 10
        assert config.retries == {'max_attempts': 2, 'mode': 'standard'}

    def test_env_var_overrides_read_timeout(self, monkeypatch):
        """LAMBDA_INVOKE_READ_TIMEOUT overrides the default read timeout."""
        monkeypatch.setenv('LAMBDA_INVOKE_READ_TIMEOUT', '120')
        server, mock_session = _reload_server_with_mock_session(monkeypatch)

        assert server.LAMBDA_INVOKE_READ_TIMEOUT == 120

        config = _client_kwargs_for(mock_session, 'lambda')['config']
        assert config.read_timeout == 120

    def test_schemas_client_shares_the_config(self, monkeypatch):
        """The schemas client is built with the same longer read timeout."""
        monkeypatch.delenv('LAMBDA_INVOKE_READ_TIMEOUT', raising=False)
        server, mock_session = _reload_server_with_mock_session(monkeypatch)

        config = _client_kwargs_for(mock_session, 'schemas')['config']
        assert config.read_timeout == 300

    @pytest.fixture(autouse=True)
    def _restore_module(self, monkeypatch):
        """Reload the module cleanly after each test so a mocked session doesn't leak."""
        yield
        # Reimport without the mocked Session left in place by monkeypatch teardown.
        import awslabs.lambda_tool_mcp_server.server as server

        importlib.reload(server)
