# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
