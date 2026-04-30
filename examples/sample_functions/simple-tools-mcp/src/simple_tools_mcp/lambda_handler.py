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
import re
from typing import Any, Dict

# Import tools to register them and get the TOOLS dict
from .tools import TOOLS


def parse_docstring_params(docstring: str) -> Dict[str, str]:
    """
    Parse parameter descriptions from docstring Args section.
    
    Args:
        docstring: Function docstring
        
    Returns:
        Dict mapping parameter names to their descriptions
    """
    param_descriptions = {}
    
    if not docstring:
        return param_descriptions
    
    # Find Args section
    args_match = re.search(r'Args:\s*\n(.*?)(?:\n\s*\n|\n\s*Returns:|\Z)', docstring, re.DOTALL)
    if not args_match:
        return param_descriptions
    
    args_section = args_match.group(1)
    
    # Parse each parameter line
    # Format: "param_name: description" or "param_name (type): description"
    param_pattern = r'^\s*(\w+)(?:\s*\([^)]+\))?\s*:\s*(.+?)(?=^\s*\w+(?:\s*\([^)]+\))?\s*:|$)'
    
    for match in re.finditer(param_pattern, args_section, re.MULTILINE | re.DOTALL):
        param_name = match.group(1)
        description = match.group(2).strip()
        # Clean up multi-line descriptions
        description = ' '.join(description.split())
        param_descriptions[param_name] = description
    
    return param_descriptions


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
        # Handle tool discovery request
        if event.get("action") == "discover_tools":
            # Get tool definitions from registered tools
            tools_list = []
            for tool_name, tool_func in TOOLS.items():
                # Extract schema from function signature and docstring
                sig = inspect.signature(tool_func)
                doc = inspect.getdoc(tool_func) or f"Tool: {tool_name}"
                
                # Parse parameter descriptions from docstring
                param_descriptions = parse_docstring_params(doc)
                
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
                    
                    # Use parsed description or fallback
                    description = param_descriptions.get(param_name, f"Parameter: {param_name}")
                    
                    properties[param_name] = {
                        "type": param_type,
                        "description": description
                    }
                    
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
                
                # Get full description (first paragraph of docstring)
                description_lines = []
                for line in doc.split('\n'):
                    line = line.strip()
                    if not line:
                        break
                    if line and not line.startswith('Args:') and not line.startswith('Returns:'):
                        description_lines.append(line)
                
                full_description = ' '.join(description_lines)
                
                tools_list.append({
                    "name": tool_name,
                    "description": full_description,
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
        if tool_name not in TOOLS:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(TOOLS.keys())
            }
        
        tool_func = TOOLS[tool_name]
        
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