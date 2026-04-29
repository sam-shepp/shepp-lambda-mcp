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
Customer Management Lambda Function with Tool Discovery Protocol

This example demonstrates how to implement the tool discovery protocol
to expose multiple tools from a single Lambda function.
"""

import json
from typing import Any, Dict


def get_tool_definitions() -> Dict[str, Any]:
    """
    Return tool definitions for the discovery protocol.
    
    This function is called when the MCP server sends {"action": "discover_tools"}
    during initialization to discover what tools this Lambda function provides.
    
    Returns:
        dict: Tool definitions with name, description, and inputSchema for each tool
    """
    return {
        "tools": [
            {
                "name": "get_customer_info",
                "description": "Retrieve detailed customer information using a customer ID. Returns customer profile including name, email, phone, address, and account status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customerId": {
                            "type": "string",
                            "description": "The unique customer identifier"
                        }
                    },
                    "required": ["customerId"]
                }
            },
            {
                "name": "get_customer_id_from_email",
                "description": "Look up a customer ID using their email address. Useful when you have an email but need the customer ID for other operations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address",
                            "format": "email"
                        }
                    },
                    "required": ["email"]
                }
            },
            {
                "name": "create_customer",
                "description": "Create a new customer account with the provided information. Returns the newly created customer ID and full customer details.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Customer's full name"
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer's email address",
                            "format": "email"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Customer's phone number"
                        },
                        "address": {
                            "type": "object",
                            "description": "Customer's address (optional)",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                                "state": {"type": "string"},
                                "zipCode": {"type": "string"}
                            }
                        }
                    },
                    "required": ["name", "email", "phone"]
                }
            },
            {
                "name": "update_customer",
                "description": "Update existing customer information. Only provided fields will be updated.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customerId": {
                            "type": "string",
                            "description": "The unique customer identifier"
                        },
                        "name": {
                            "type": "string",
                            "description": "Customer's full name (optional)"
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer's email address (optional)",
                            "format": "email"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Customer's phone number (optional)"
                        },
                        "address": {
                            "type": "object",
                            "description": "Customer's address (optional)",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                                "state": {"type": "string"},
                                "zipCode": {"type": "string"}
                            }
                        }
                    },
                    "required": ["customerId"]
                }
            }
        ]
    }


def get_customer_info(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve customer information by ID.
    
    Args:
        arguments: Dict containing customerId
        
    Returns:
        dict: Customer information or error
    """
    customer_id = arguments.get("customerId")
    
    if not customer_id:
        return {"error": "Missing required field: customerId"}
    
    # Mock database lookup
    # In a real implementation, this would query a database
    mock_customers = {
        "12345": {
            "customerId": "12345",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zipCode": "12345"
            },
            "accountStatus": "active",
            "accountCreated": "2024-01-15"
        },
        "67890": {
            "customerId": "67890",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-987-6543",
            "address": {
                "street": "456 Oak Ave",
                "city": "Springfield",
                "state": "IL",
                "zipCode": "62701"
            },
            "accountStatus": "active",
            "accountCreated": "2024-03-20"
        }
    }
    
    customer = mock_customers.get(customer_id)
    if customer:
        return customer
    else:
        return {"error": f"Customer not found with ID: {customer_id}"}


def get_customer_id_from_email(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up customer ID by email address.
    
    Args:
        arguments: Dict containing email
        
    Returns:
        dict: Customer ID or error
    """
    email = arguments.get("email")
    
    if not email:
        return {"error": "Missing required field: email"}
    
    # Mock email to ID mapping
    # In a real implementation, this would query a database
    email_to_id = {
        "john.doe@example.com": "12345",
        "jane.smith@example.com": "67890"
    }
    
    customer_id = email_to_id.get(email.lower())
    if customer_id:
        return {"customerId": customer_id, "email": email}
    else:
        return {"error": f"No customer found with email: {email}"}


def create_customer(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new customer account.
    
    Args:
        arguments: Dict containing name, email, phone, and optional address
        
    Returns:
        dict: Created customer information or error
    """
    name = arguments.get("name")
    email = arguments.get("email")
    phone = arguments.get("phone")
    address = arguments.get("address")
    
    # Validate required fields
    if not all([name, email, phone]):
        return {"error": "Missing required fields: name, email, and phone are required"}
    
    # Validate address if provided
    if address:
        required_address_fields = ["street", "city", "state", "zipCode"]
        if not all(field in address for field in required_address_fields):
            return {
                "error": "Address is missing required fields (street, city, state, zipCode)"
            }
    
    # Mock customer creation
    # In a real implementation, this would insert into a database
    new_customer = {
        "customerId": "98765",  # Would be auto-generated in real implementation
        "name": name,
        "email": email,
        "phone": phone,
        "accountStatus": "active",
        "accountCreated": "2026-04-29"
    }
    
    if address:
        new_customer["address"] = address
    
    return new_customer


def update_customer(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing customer information.
    
    Args:
        arguments: Dict containing customerId and optional fields to update
        
    Returns:
        dict: Updated customer information or error
    """
    customer_id = arguments.get("customerId")
    
    if not customer_id:
        return {"error": "Missing required field: customerId"}
    
    # Mock customer update
    # In a real implementation, this would update a database record
    updated_fields = {k: v for k, v in arguments.items() if k != "customerId" and v is not None}
    
    if not updated_fields:
        return {"error": "No fields provided to update"}
    
    # Return mock updated customer
    result = {
        "customerId": customer_id,
        "updated": True,
        "updatedFields": list(updated_fields.keys()),
        "message": f"Successfully updated customer {customer_id}"
    }
    
    return result


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler with tool discovery protocol support.
    
    This handler demonstrates the tool discovery protocol:
    1. Responds to {"action": "discover_tools"} with tool definitions
    2. Routes tool invocations based on the "tool" field
    3. Supports both new format {"tool": "...", "arguments": {...}}
       and legacy format with flat parameters
    
    Args:
        event: Lambda event containing action, tool, or parameters
        context: AWS Lambda context object
        
    Returns:
        dict: Tool definitions, tool results, or error message
    """
    try:
        # Handle tool discovery request
        if event.get("action") == "discover_tools":
            return get_tool_definitions()
        
        # Determine tool name and arguments
        if "arguments" in event:
            # New format: {"tool": "...", "arguments": {...}}
            tool_name = event.get("tool")
            arguments = event["arguments"]
        else:
            # Legacy format: {"tool": "...", "customerId": "...", ...}
            tool_name = event.get("tool")
            arguments = {k: v for k, v in event.items() if k != "tool"}
        
        # Route to appropriate tool handler
        if tool_name == "get_customer_info":
            return get_customer_info(arguments)
        elif tool_name == "get_customer_id_from_email":
            return get_customer_id_from_email(arguments)
        elif tool_name == "create_customer":
            return create_customer(arguments)
        elif tool_name == "update_customer":
            return update_customer(arguments)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": [
                    "get_customer_info",
                    "get_customer_id_from_email",
                    "create_customer",
                    "update_customer"
                ]
            }
            
    except Exception as e:
        return {
            "error": "Internal error",
            "message": str(e)
        }
