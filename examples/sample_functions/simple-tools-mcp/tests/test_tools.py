"""Tests for Simple Tools MCP Server tools."""

import json
import pytest
from simple_tools_mcp.tools import calculate, echo, get_timestamp, hello_world


class TestHelloWorld:
    """Tests for hello_world tool."""

    def test_hello_world_default(self):
        """Test hello_world with default name."""
        result = hello_world()
        data = json.loads(result)
        assert data["greeting"] == "Hello, World!"
        assert "tool" in data
        assert data["tool"] == "hello_world"

    def test_hello_world_custom_name(self):
        """Test hello_world with custom name."""
        result = hello_world(name="Alice")
        data = json.loads(result)
        assert data["greeting"] == "Hello, Alice!"


class TestEcho:
    """Tests for echo tool."""

    def test_echo_basic(self):
        """Test basic echo."""
        result = echo(message="test")
        data = json.loads(result)
        assert data["original"] == "test"
        assert data["echoed"] == "test"
        assert data["uppercase"] is False
        assert data["repeat_count"] == 1

    def test_echo_uppercase(self):
        """Test echo with uppercase."""
        result = echo(message="test", uppercase=True)
        data = json.loads(result)
        assert data["echoed"] == "TEST"
        assert data["uppercase"] is True

    def test_echo_repeat(self):
        """Test echo with repeat."""
        result = echo(message="hi", repeat=3)
        data = json.loads(result)
        assert data["echoed"] == "hi hi hi"
        assert data["repeat_count"] == 3

    def test_echo_invalid_repeat(self):
        """Test echo with invalid repeat count."""
        result = echo(message="test", repeat=20)
        data = json.loads(result)
        assert "error" in data


class TestGetTimestamp:
    """Tests for get_timestamp tool."""

    def test_timestamp_iso(self):
        """Test ISO format timestamp."""
        result = get_timestamp(format="iso")
        data = json.loads(result)
        assert "timestamp" in data
        assert data["format"] == "ISO 8601"
        assert data["timestamp"].endswith("Z")

    def test_timestamp_unix(self):
        """Test Unix format timestamp."""
        result = get_timestamp(format="unix")
        data = json.loads(result)
        assert "timestamp" in data
        assert data["format"] == "Unix epoch (seconds)"
        assert isinstance(data["timestamp"], int)

    def test_timestamp_readable(self):
        """Test readable format timestamp."""
        result = get_timestamp(format="readable")
        data = json.loads(result)
        assert "timestamp" in data
        assert data["format"] == "Human readable"
        assert "UTC" in data["timestamp"]

    def test_timestamp_invalid_format(self):
        """Test invalid format."""
        result = get_timestamp(format="invalid")
        data = json.loads(result)
        assert "error" in data


class TestCalculate:
    """Tests for calculate tool."""

    def test_calculate_add(self):
        """Test addition."""
        result = calculate(operation="add", a=5, b=3)
        data = json.loads(result)
        assert data["result"] == 8
        assert data["operation"] == "add"

    def test_calculate_subtract(self):
        """Test subtraction."""
        result = calculate(operation="subtract", a=10, b=4)
        data = json.loads(result)
        assert data["result"] == 6

    def test_calculate_multiply(self):
        """Test multiplication."""
        result = calculate(operation="multiply", a=7, b=6)
        data = json.loads(result)
        assert data["result"] == 42

    def test_calculate_divide(self):
        """Test division."""
        result = calculate(operation="divide", a=20, b=4)
        data = json.loads(result)
        assert data["result"] == 5

    def test_calculate_divide_by_zero(self):
        """Test division by zero."""
        result = calculate(operation="divide", a=10, b=0)
        data = json.loads(result)
        assert "error" in data

    def test_calculate_invalid_operation(self):
        """Test invalid operation."""
        result = calculate(operation="power", a=2, b=3)
        data = json.loads(result)
        assert "error" in data
