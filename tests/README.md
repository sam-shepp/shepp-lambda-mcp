# shepp-lambda-mcp Tests

This directory contains the test suite for `shepp-lambda-mcp`. The tests target the
current `ChukMCPServer`-based server (`awslabs/lambda_tool_mcp_server/server.py`),
including the tool-discovery protocol and the legacy single-tool fallback.

## Test structure

| File | Covers |
| --- | --- |
| `test_server.py` | Pure helpers: `validate_function_name`, `sanitize_tool_name`, `format_lambda_response` (tool-aware, 3-arg), and the `main` entrypoint |
| `test_invoke.py` | `invoke_lambda_tool_impl` (the `{'tool', 'arguments'}` envelope + string-parameter parsing) and the legacy `invoke_lambda_function_impl` |
| `test_discovery.py` | `discover_tools_from_lambda`, `create_lambda_tool_from_discovery`, and `create_legacy_lambda_tool`, including that registered handlers delegate to the right invoke impl |
| `test_register.py` | `register_lambda_functions` (prefix/list/tag filters, incomplete-tag warning, discovery-vs-legacy path, error handling), `filter_functions_by_tag`, and `get_all_lambda_functions` pagination |
| `test_schema.py` | EventBridge Schema Registry integration: `get_schema_from_registry`, `get_schema_arn_from_function_arn` |
| `test_client_config.py` | The boto3 client `Config` (read/connect timeout, retries) and how the module selects credentials (explicit / profile / default chain) |

## Running the tests

The project uses [`uv`](https://docs.astral.sh/uv/). From the repo root:

```bash
uv run pytest
```

Coverage (against `awslabs.lambda_tool_mcp_server`) and `term-missing` reporting are
enabled by default via `addopts` in `pyproject.toml`, so a plain run already prints
coverage. To run without coverage:

```bash
uv run pytest --no-cov
```

Run a single file, class, or test:

```bash
uv run pytest tests/test_register.py
uv run pytest tests/test_server.py::TestValidateFunctionName
uv run pytest tests/test_server.py::TestValidateFunctionName::test_empty_prefix_and_list
```

For an HTML coverage report:

```bash
uv run pytest --cov-report=html
# then open htmlcov/index.html
```

## Fixtures

Fixtures live in `conftest.py`:

- `sample_functions` — the list of Lambda function objects (name, ARN, description) used across tests.
- `mock_lambda_client` — a mock boto3 Lambda client. Its `invoke` answers both the
  discovery probe (`{'action': 'discover_tools'}`) and normal tool/legacy invokes.
  By default no function advertises tools, so registration takes the legacy path;
  tests that exercise discovery patch `discover_tools_from_lambda` directly.
- `server_module` — imports the server (under a mocked `boto3.Session`) and clears the
  shared `mcp` tool registry before and after the test, so real tool registrations
  don't leak between tests.

## Import-time note

`server.py` builds its boto3 clients at import time, so every test module imports it
under a mocked `boto3.Session` (a `pytest.MonkeyPatch().context()` guard at the top of
each file). `test_client_config.py` additionally reloads the module with `importlib`
to assert how the clients and session are constructed for different environments.

## Guidelines for new tests

1. Put tests in the file matching the area under test (see the table above).
2. Prefer asserting against real registrations via `mcp.get_tools()` over asserting
   that a decorator was called — it verifies the handler wiring end to end.
3. Patch `awslabs.lambda_tool_mcp_server.server.lambda_client` (and `schemas_client`)
   rather than reaching for real AWS calls.
4. Use `@pytest.mark.asyncio` for the async invoke paths.
5. Keep Google-style docstrings on test classes and methods (enforced by ruff).
