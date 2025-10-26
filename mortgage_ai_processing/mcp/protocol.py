"""
MCP protocol handler implementation.

Handles MCP (Model Context Protocol) message parsing, validation,
and response formatting according to the MCP specification.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import json
import logging
from enum import Enum


class MCPMessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MCPErrorCode(Enum):
    """Standard MCP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000


@dataclass
class MCPToolInfo:
    """Tool information for MCP protocol."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class MCPServerInfo:
    """Server information for MCP protocol."""
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None


@dataclass
class MCPCapabilities:
    """Server capabilities for MCP protocol."""
    tools: Dict[str, Any]
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


class MCPProtocolHandler:
    """
    Handles MCP protocol message parsing, validation, and formatting.
    
    Provides utilities for:
    - Message validation
    - Request/response formatting
    - Error handling
    - Protocol compliance
    """
    
    def __init__(self):
        self.logger = logging.getLogger("mcp_protocol")
        
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate MCP request format.
        
        Args:
            request_data: Request data to validate
            
        Returns:
            True if request is valid
        """
        required_fields = ["jsonrpc", "method"]
        
        # Check required fields
        for field in required_fields:
            if field not in request_data:
                self.logger.error(f"Missing required field: {field}")
                return False
                
        # Validate JSON-RPC version
        if request_data.get("jsonrpc") != "2.0":
            self.logger.error(f"Invalid JSON-RPC version: {request_data.get('jsonrpc')}")
            return False
            
        # Validate method name
        method = request_data.get("method")
        if not isinstance(method, str) or not method:
            self.logger.error(f"Invalid method name: {method}")
            return False
            
        return True
        
    def create_response(self, 
                       result: Optional[Dict[str, Any]] = None,
                       error: Optional[Dict[str, Any]] = None,
                       request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create MCP response.
        
        Args:
            result: Response result data
            error: Error information if any
            request_id: ID from original request
            
        Returns:
            Formatted MCP response
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        if error is not None:
            response["error"] = error
        else:
            response["result"] = result or {}
            
        return response
        
    def create_error_response(self, 
                            code: MCPErrorCode,
                            message: str,
                            data: Optional[Dict[str, Any]] = None,
                            request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create MCP error response.
        
        Args:
            code: Error code
            message: Error message
            data: Additional error data
            request_id: ID from original request
            
        Returns:
            Formatted MCP error response
        """
        error = {
            "code": code.value,
            "message": message
        }
        
        if data is not None:
            error["data"] = data
            
        return self.create_response(error=error, request_id=request_id)
        
    def format_tools_list_response(self, tools: List[MCPToolInfo]) -> Dict[str, Any]:
        """
        Format tools/list response.
        
        Args:
            tools: List of tool information
            
        Returns:
            Formatted tools list response
        """
        return {
            "tools": [asdict(tool) for tool in tools]
        }
        
    def format_tool_call_response(self, 
                                content: str,
                                is_error: bool = False) -> Dict[str, Any]:
        """
        Format tools/call response.
        
        Args:
            content: Response content
            is_error: Whether this is an error response
            
        Returns:
            Formatted tool call response
        """
        return {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ],
            "isError": is_error
        }
        
    def format_server_info_response(self, server_info: MCPServerInfo) -> Dict[str, Any]:
        """
        Format server/info response.
        
        Args:
            server_info: Server information
            
        Returns:
            Formatted server info response
        """
        return asdict(server_info)
        
    def format_capabilities_response(self, capabilities: MCPCapabilities) -> Dict[str, Any]:
        """
        Format server/capabilities response.
        
        Args:
            capabilities: Server capabilities
            
        Returns:
            Formatted capabilities response
        """
        return {
            "capabilities": asdict(capabilities)
        }
        
    def parse_tool_call_params(self, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Parse tools/call parameters.
        
        Args:
            params: Request parameters
            
        Returns:
            Tuple of (tool_name, arguments)
            
        Raises:
            ValueError: If parameters are invalid
        """
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Tool name is required")
            
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")
            
        return tool_name, arguments
        
    def validate_tool_call_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate tools/call parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            True if parameters are valid
        """
        try:
            self.parse_tool_call_params(params)
            return True
        except ValueError as e:
            self.logger.error(f"Invalid tool call parameters: {str(e)}")
            return False
            
    def create_notification(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create MCP notification.
        
        Args:
            method: Notification method
            params: Notification parameters
            
        Returns:
            Formatted MCP notification
        """
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
    def is_notification(self, message: Dict[str, Any]) -> bool:
        """
        Check if message is a notification.
        
        Args:
            message: Message to check
            
        Returns:
            True if message is a notification
        """
        return "id" not in message and "method" in message
        
    def extract_request_id(self, request: Dict[str, Any]) -> Optional[str]:
        """
        Extract request ID from request.
        
        Args:
            request: Request data
            
        Returns:
            Request ID if present
        """
        return request.get("id")
        
    def log_protocol_message(self, 
                           message_type: MCPMessageType,
                           method: Optional[str] = None,
                           success: bool = True,
                           error: Optional[str] = None) -> None:
        """
        Log protocol message for debugging.
        
        Args:
            message_type: Type of message
            method: Method name if applicable
            success: Whether operation was successful
            error: Error message if any
        """
        log_msg = f"MCP {message_type.value}"
        if method:
            log_msg += f" - {method}"
            
        if success:
            self.logger.debug(log_msg + " - SUCCESS")
        else:
            self.logger.error(log_msg + f" - ERROR: {error}")
            
    def get_supported_methods(self) -> List[str]:
        """
        Get list of supported MCP methods.
        
        Returns:
            List of supported method names
        """
        return [
            "tools/list",
            "tools/call", 
            "server/info",
            "server/capabilities"
        ]