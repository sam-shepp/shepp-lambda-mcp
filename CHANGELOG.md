# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.2] - 2026-10-06

### Changed

- Successful Lambda tool responses now return plain compact JSON text without tool names, internal Lambda function names, or pretty-printing.
- Non-JSON payloads are returned as undecorated text.

## [2.3.1] - 2026-10-04

### Fixed

- Zero-argument discovered tools no longer get a spurious required `parameters: dict` argument from the generic fallback wrapper. `build_signature_from_schema` previously returned `None` both for a schema with no properties (a genuinely zero-argument tool) and for one whose properties couldn't be synthesised into a signature, so `create_lambda_tool_from_discovery` treated both the same way and fell back to `tool_handler(parameters: dict)` with no default. ChukMCPServer then advertised `parameters` as a required object field, so a correct zero-arg call with `arguments={}` failed validation with `Invalid parameter 'parameters': expected object, got NoneType`. The two cases are now distinguished: a schema with missing/empty properties registers a true zero-parameter handler that invokes the Lambda tool with `{}`.
- The generic `parameters` fallback wrapper (now reserved for schemas that genuinely can't be synthesised, e.g. a property name that isn't a valid Python identifier) defaults `parameters` to `None` instead of leaving it required.
- A legacy caller still sending `{"parameters": {}}` to a zero-arg tool is unaffected: ChukMCPServer only validates arguments against the handler's declared parameters, so the stray key is ignored rather than rejected.

## [2.3.0] - 2026-08-03

### Changed

- Discovered tools now advertise their `inputSchema` as flat, top-level parameters instead of a generic `parameters` object wrapper. ChukMCPServer derives a tool's advertised MCP input schema from its handler's Python signature, so the server now synthesises a signature from each discovered tool's `inputSchema`. LLMs — which are trained to emit flat tool arguments matching the schema — can now call tools naturally (e.g. `{"city": "London"}`) rather than nesting arguments under `parameters`. Supplied arguments are forwarded downstream unchanged as `{"tool": <name>, "arguments": {...}}`.
- Tools whose `inputSchema` has no usable properties (or a property name that isn't a valid Python identifier) fall back to the previous single `parameters` object argument. Legacy (non-discovery) functions are unchanged.

## [2.2.2] - 2026-08-03

### Fixed

- Give the boto3 Lambda (and Schemas) client a longer, env-configurable read timeout. Previously the client used boto3's default 60s read timeout, so synchronous invokes of legitimately slow downstream MCP-server Lambdas (e.g. long-running wx.data/Presto query tools) would raise `Read timeout on endpoint URL` even though the downstream function — which carries its own multi-minute timeout — was still running successfully. The read timeout now defaults to 300s and is overridable via the `LAMBDA_INVOKE_READ_TIMEOUT` environment variable. `connect_timeout` is set to 10s and the client retries with `max_attempts=2` (standard mode).

## [1.0.0] - 2025-05-26

### Removed

- **BREAKING CHANGE:** Server Sent Events (SSE) support has been removed in accordance with the Model Context Protocol specification's [backwards compatibility guidelines](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#backwards-compatibility)
- This change prepares for future support of [Streamable HTTP](https://modelcontextprotocol.io/specification/draft/basic/transports#streamable-http) transport

## [2.1.0] - 2026-04-29

### Added

- **Tool Discovery Protocol**: Lambda functions can now expose multiple tools instead of being limited to one tool per function
- Lambda functions can implement a discovery endpoint by responding to `{"action": "discover_tools"}` with tool definitions
- Each discovered tool includes name, description, and JSON Schema for input validation
- Backward compatibility maintained for Lambda functions that don't implement the discovery protocol
- Enhanced tool naming: discovered tools are prefixed with function name to avoid conflicts (e.g., `astra_race_vector_search`)

### Changed

- Tool invocation now uses `{"tool": "tool_name", "arguments": {...}}` format for discovered tools
- Legacy flat parameter format still supported for backward compatibility
- Tool descriptions are now more detailed and include input schemas when available
- Improved error handling with custom exception classes for better error reporting
- Enhanced logging throughout the application for better debugging and monitoring

### Documentation

- Added `TOOL_DISCOVERY_PROTOCOL.md` documenting the discovery protocol specification
- Updated Lambda handler examples to show tool discovery implementation

## Unreleased

### Added

- Initial project setup
