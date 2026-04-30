# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
AWS Lambda Handler for Simple Tools MCP Server

This handler allows the MCP server to be deployed as an AWS Lambda function
while maintaining compatibility with the tool discovery protocol.
"""

import inspect
import json
from typing import Any, Dict

from chuk_mcp_server import get_mcp_instance

# Import tools to register them
from . import tools  # noqa: F401


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler that supports tool discovery protocol.
    
    This handler allows the Lambda function to work with shepp-lambda-mcp
    by responding to discovery requests and routing tool invocations.
    
    Args:
        event: Lambda event containing action, tool, or parameters
        context: AWS Lambda context object
        
    Returns:
        dict: Tool definitions, tool results, or error message
    """
    try:
        # Get the MCP instance
        mcp = get_mcp_instance()
        
        # Handle tool discovery request
        if event.get("action") == "discover_tools":
            # Get tool definitions from ChukMCPServer
            tools_list = []
            for tool_name, tool_func in mcp._tools.items():
                # Extract schema from function signature and docstring
                sig = inspect.signature(tool_func)
                doc = inspect.getdoc(tool_func) or f"Tool: {tool_name}"
                
                # Build input schema from function signature
                properties = {}
                required = []
                
                for param_name, param in sig.parameters.items():
                    if param_name in ['self', 'ctx']:
                        continue
                    
                    param_type = "string"  # Default type
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                    
                    properties[param_name] = {
                        "type": param_type,
                        "description": f"Parameter: {param_name}"
                    }
                    
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
                
                tools_list.append({
                    "name": tool_name,
                    "description": doc.split('\n')[0],  # First line of docstring
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                })
            
            return {"tools": tools_list}
        
        # Handle tool invocation
        tool_name = event.get("tool")
        if not tool_name:
            return {"error": "Missing 'tool' field in request"}
        
        # Get arguments (support both formats)
        if "arguments" in event:
            arguments = event["arguments"]
        else:
            arguments = {k: v for k, v in event.items() if k != "tool"}
        
        # Get the tool function
        if tool_name not in mcp._tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(mcp._tools.keys())
            }
        
        tool_func = mcp._tools[tool_name]
        
        # Invoke the tool
        result = tool_func(**arguments)
        
        # Parse result if it's JSON string
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError:
            return {"result": result}
            
    except Exception as e:
        return {
            "error": "Internal error",
            "message": str(e),
            "type": type(e).__name__
        }


__all__ = ["lambda_handler"]