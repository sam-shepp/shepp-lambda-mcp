"""Tests for the boto3 client configuration (read timeout) of the lambda-tool-mcp-server."""

import importlib
import pytest
from unittest.mock import MagicMock


def _reload_server_with_mock_session(monkeypatch):
    """Reload the server module with boto3.Session mocked out.

    Returns the reloaded server module and the mock Session instance so tests can
    inspect the arguments the module used to build its boto3 clients at import time.
    """
    _, instance, _ = _reload_server_capturing_session(monkeypatch)
    import awslabs.lambda_tool_mcp_server.server as server

    return server, instance


def _reload_server_capturing_session(monkeypatch):
    """Reload the server module, returning (server, Session instance, Session class mock).

    Exposing the Session class mock lets tests assert how the module chose to build the
    boto3 session (explicit credentials vs profile vs default chain) at import time.
    """
    mock_session_instance = MagicMock()
    mock_session_cls = MagicMock(return_value=mock_session_instance)
    monkeypatch.setattr('boto3.Session', mock_session_cls)

    import awslabs.lambda_tool_mcp_server.server as server

    server = importlib.reload(server)
    return server, mock_session_instance, mock_session_cls


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


class TestSessionCredentialSelection:
    """Tests for how the module builds its boto3 Session from the environment."""

    def test_explicit_credentials(self, monkeypatch):
        """Explicit access key/secret build a Session from those credentials."""
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'AKIAEXAMPLE')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'secret')
        monkeypatch.setenv('AWS_SESSION_TOKEN', 'token')
        monkeypatch.setenv('AWS_REGION', 'us-west-2')
        monkeypatch.delenv('AWS_PROFILE', raising=False)

        _, _, session_cls = _reload_server_capturing_session(monkeypatch)

        session_cls.assert_called_once_with(
            aws_access_key_id='AKIAEXAMPLE',
            aws_secret_access_key='secret',
            aws_session_token='token',
            region_name='us-west-2',
        )

    def test_profile(self, monkeypatch):
        """With no explicit credentials, a profile builds a profile-based Session."""
        monkeypatch.delenv('AWS_ACCESS_KEY_ID', raising=False)
        monkeypatch.delenv('AWS_SECRET_ACCESS_KEY', raising=False)
        monkeypatch.setenv('AWS_PROFILE', 'my-profile')
        monkeypatch.setenv('AWS_REGION', 'eu-west-1')

        _, _, session_cls = _reload_server_capturing_session(monkeypatch)

        session_cls.assert_called_once_with(profile_name='my-profile', region_name='eu-west-1')

    def test_default_chain(self, monkeypatch):
        """With neither credentials nor profile, the default chain is used."""
        monkeypatch.delenv('AWS_ACCESS_KEY_ID', raising=False)
        monkeypatch.delenv('AWS_SECRET_ACCESS_KEY', raising=False)
        monkeypatch.delenv('AWS_PROFILE', raising=False)
        monkeypatch.setenv('AWS_REGION', 'ap-south-1')

        _, _, session_cls = _reload_server_capturing_session(monkeypatch)

        session_cls.assert_called_once_with(region_name='ap-south-1')

    @pytest.fixture(autouse=True)
    def _restore_module(self, monkeypatch):
        """Reload the module cleanly after each test so a mocked session doesn't leak."""
        yield
        import awslabs.lambda_tool_mcp_server.server as server

        importlib.reload(server)
