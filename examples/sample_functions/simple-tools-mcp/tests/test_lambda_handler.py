"""Tests for Lambda handler."""

import json
import pytest
from simple_tools_mcp.lambda_handler import lambda_handler


class TestLambdaHandler:
    """Tests for AWS Lambda handler."""

    def test_discover_tools(self):
        """Test tool discovery."""
        event = {"action": "discover_tools"}
        result = lambda_handler(event, None)
        
        assert "tools" in result
        assert len(result["tools"]) == 4
        
        tool_names = [tool["name"] for tool in result["tools"]]
        assert "hello_world" in tool_names
        assert "echo" in tool_names
        assert "get_timestamp" in tool_names
        assert "calculate" in tool_names

    def test_invoke_hello_world(self):
        """Test invoking hello_world tool."""
        event = {
            "tool": "hello_world",
            "arguments": {"name": "Lambda"}
        }
        result = lambda_handler(event, None)
        
        assert "greeting" in result
        assert result["greeting"] == "Hello, Lambda!"

    def test_invoke_echo(self):
        """Test invoking echo tool."""
        event = {
            "tool": "echo",
            "arguments": {
                "message": "test",
                "uppercase": True
            }
        }
        result = lambda_handler(event, None)
        
        assert result["echoed"] == "TEST"

    def test_invoke_calculate(self):
        """Test invoking calculate tool."""
        event = {
            "tool": "calculate",
            "arguments": {
                "operation": "multiply",
                "a": 6,
                "b": 7
            }
        }
        result = lambda_handler(event, None)
        
        assert result["result"] == 42

    def test_missing_tool(self):
        """Test missing tool field."""
        event = {"arguments": {"name": "test"}}
        result = lambda_handler(event, None)
        
        assert "error" in result

    def test_unknown_tool(self):
        """Test unknown tool."""
        event = {
            "tool": "unknown_tool",
            "arguments": {}
        }
        result = lambda_handler(event, None)
        
        assert "error" in result
        assert "available_tools" in result
